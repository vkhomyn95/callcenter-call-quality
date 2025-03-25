import logging
import os
from datetime import datetime, timezone
from io import BytesIO

from celery import Task
from elevenlabs import ElevenLabs
from openai import OpenAI

from celery_worker.database.database import pymysql_db
from celery_worker.hook.hooker import validate_url, send_webhook
from celery_worker.variables import variables
from celery_worker.worker.start import celery

# whisper = WhisperModelProcessor()
elevenlabs = ElevenLabs(api_key=variables.elevenlabs_api_key)
client = OpenAI(api_key=variables.openai_api_key)


class CallbackTask(Task):

    def on_success(self, retval, task_id, args, kwargs):
        """
        Called when the task completes successfully.

        :param retval: Return value of the task.
        :param task_id: Unique id of the executed task.
        :param args: Original positional arguments of the task.
        :param kwargs: Original keyword arguments of the task.
        """
        user = self._load_user(retval["user_id"])
        postback_url = None

        if user and user["origin"] is not None:
            postback_url = user["origin"]

        if "origin" in retval and retval["origin"] is not None:
            postback_url = retval["origin"]

        if postback_url and self._is_valid_url(postback_url):
            retval.update({"task_id": task_id, "status": "SUCCESS"})
            self._send_webhook(
                url=postback_url,
                auth=user["api_key"],
                payload=retval
            )
        else:
            logging.error(f" >> Success Not valid postback url for user_id: {retval['user_id']}")

    def on_failure(self, exc, task_id, args, kwargs, err_info):
        """
        Called when the task fails.

        :param exc: The exception raised by the task.
        :param task_id: Unique id of the failed task.
        :param args: Original positional arguments of the task.
        :param kwargs: Original keyword arguments of the task.
        :param err_info: Exception info object.
        """
        received_date, duration, num_channels, user_id, talk_record_id, resampler, unique_uuid, origin = args

        user = self._load_user(user_id)
        postback_url = None

        if user and user["origin"] is not None:
            postback_url = user["origin"]

        if origin is not None:
            postback_url = origin

        if postback_url and self._is_valid_url(postback_url):
            self._send_webhook(
                url=postback_url,
                auth=user["api_key"],
                payload={
                    "status": "FAILURE",
                    "talk_record_id": talk_record_id,
                    "user_id": user_id,
                    "task_id": task_id,
                    "error": str(exc)
                }
            )
        else:
            logging.error(f" >> Failure Not valid postback url for user_id: {user_id}")

    def _load_user(self, user_id):
        """
        Fetches user details from the database.

        :param user_id: ID of the user to be fetched.
        :return: User data or None.
        """
        try:
            return pymysql_db.load_user_postback_info_by_id(user_id)
        except Exception as e:
            logging.error(f" >> Database error fetching user {user_id}: {e}")
            return None

    def _is_valid_url(self, url):
        """
        Validates if the provided URL is in the correct format.

        :param url: URL string to validate.
        :return: Boolean indicating whether the URL is valid.
        """
        try:
            return validate_url(url)
        except ValueError:
            return False

    def _send_webhook(self, url, auth, payload):
        """
        Sends the webhook request.

        :param url: Webhook URL to send the request to.
        :param auth: API key or auth token for the webhook.
        :param payload: The data payload to be sent.
        """
        try:
            send_webhook(
                webhook_payload={
                    "url": url,
                    "auth": auth,
                    "payload": payload
                }
            )
        except Exception as e:
            logging.error(f" >> Error sending webhook: {e}")


@celery.task(base=CallbackTask, name="transcribe_scribe_v1", queue="scribe_v1_queue", bind=True)
def transcribe_scribe_v1(self, received_date, duration, num_channels, user_id, talk_record_id, resampler, unique_uuid, origin):
    """
    Transcription task that processes audio files and returns transcription results.

    :param received_date: The date the file was received.
    :param duration: Duration of the audio file.
    :param num_channels: Number of audio channels.
    :param user_id: ID of the user requesting transcription.
    :param talk_record_id: ID of the talk record.
    :param resampler: Resampled audio file paths.
    :param unique_uuid: Unique ID for this transcription request.
    :param origin: Origin URL for postback.
    :return: A dictionary with transcription metadata and results.
    """
    transcription_results = {"words": []}
    transcription_date = datetime.now(timezone.utc).isoformat()[:-9]

    for file_path in resampler:
        logging.info(f" >> Transcribing file {file_path} for request {unique_uuid}.")
        # transcription = process_transcription(os.path.join(get_save_directory(received_date), file_path))

        try:
            with open(os.path.join(get_save_directory(received_date), file_path), 'rb') as audio_file:
                audio_data = BytesIO(audio_file.read())

            transcription = elevenlabs.speech_to_text.convert(
                file=audio_data,
                model_id="scribe_v1",
                tag_audio_events=True,
                num_speakers=2,
                diarize=True
            )
            # print(transcription)
            transcription_results["words"] = transcription.words
            # return transcription.text
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
            return None
    return {
        "model": "scribe_v1",
        "received_date": received_date,
        "transcription_date": transcription_date,
        "start_transcription_date": received_date,
        "duration": duration,
        "num_channels": num_channels,
        "user_id": user_id,
        "talk_record_id": talk_record_id,
        "transcription": split_replies_by_scribe(transcription_results),
        "unique_uuid": unique_uuid,
        "origin": origin
    }


@celery.task(name="transcribe_openai_whisper", queue="openai_whisper_queue", bind=True)
def transcribe_openai_whisper(self, received_date, duration, num_channels, user_id, talk_record_id, resampler, unique_uuid, origin):
    """
    Transcription using OpenAI Whisper
    """
    transcription_results = {"segments": []}
    transcription_date = datetime.now(timezone.utc).isoformat()[:-9]

    for file_path in resampler:
        try:
            with open(os.path.join(get_save_directory(received_date), file_path), 'rb') as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )

            transcription_results["segments"] = transcription.segments

        except Exception as e:
            logging.error(f"OpenAI error processing file {file_path}: {e}")
            raise self.retry(exc=e)

    return {
        "model": "openai_whisper",
        "received_date": received_date,
        "transcription_date": transcription_date,
        "duration": duration,
        "num_channels": num_channels,
        "user_id": user_id,
        "talk_record_id": talk_record_id,
        "transcription": split_replies_by_openai(transcription_results),
        "unique_uuid": unique_uuid,
        "origin": origin
    }

# def process_transcription(file_path):
#     """
#     Helper function to process the transcription of a file.
#
#     :param file_path: The file path to the audio file.
#     :return: The transcription result without the 'text' key.
#     """
#
#     transcription = whisper.pipe(file_path, return_timestamps=True)
#     print(transcription)
#     transcription.pop('text', None)
#     return transcription


def get_save_directory(received_date):
    # Create directory path based on received date (year/month/day)
    year, month, day = received_date.split('T')[0].split("-")
    save_dir = os.path.join(variables.file_dir, year, month, day)

    # Create the directories if they do not exist
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


def split_replies_by_scribe(transcription_results):
    """
    Об'єднує слова у репліки на основі speaker_id та розбиває їх, якщо є поле "characters".

    :param transcription_results: Список слів із транскрипції.
    :return: Список реплік, кожна з яких містить текст, часовий інтервал та ідентифікатор спікера.
    """
    import re

    replies = []
    current_reply = None

    for word in transcription_results.get("words", []):
        speaker = int(re.search(r'\d+', word.speaker_id).group()) if re.search(r'\d+', word.speaker_id) else 0

        if current_reply is None or current_reply["speaker_id"] != speaker:
            # Початок нової репліки
            if current_reply:
                replies.append(current_reply)
            current_reply = {
                "text": word.text,
                "start": word.start,
                "end": word.end,
                "speaker_id": speaker
            }
        else:
            # Продовження поточної репліки
            current_reply["text"] += " " + word.text
            current_reply["end"] = word.end

        # Якщо є ключ "characters", це означає кінець репліки
        if "characters" in word:
            replies.append(current_reply)
            current_reply = None

    # Додаємо останню репліку, якщо вона є
    if current_reply:
        replies.append(current_reply)
    return replies


def split_replies_by_openai(transcription_results):
    """
    Об'єднує слова у репліки на основі speaker_id та розбиває їх, якщо є поле "characters".

    :param transcription_results: Список слів із транскрипції.
    :return: Список реплік, кожна з яких містить текст, часовий інтервал та ідентифікатор спікера.
    """

    replies = []

    for word in transcription_results.get("segments", []):
        replies.append({
            "text": word.text,
            "start": word.start,
            "end": word.end,
            "speaker_id": 0
        })

    return replies


