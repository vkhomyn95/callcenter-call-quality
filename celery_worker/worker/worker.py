import logging
import os
from datetime import datetime, timezone

from celery import Task
from celery.states import SUCCESS

from celery_worker.database import mariadb
from celery_worker.hook.hooker import validate_url, send_webhook
from celery_worker.models.whsiper import WhisperModelProcessor
from celery_worker.variables import variables
from celery_worker.worker.start import celery


whisper = WhisperModelProcessor()


class CallbackTask(Task):

    def on_success(self, retval, task_id, args, kwargs):
        """
        retval – The return value of the task.
        task_id – Unique id of the executed task.
        args – Original arguments for the executed task.
        kwargs – Original keyword arguments for the executed task.
        """

        user = mariadb.load_user_by_id(retval["user_id"])

        if user and user.api_key and retval["origin"]:
            try:
                validate_url(retval["origin"])
            except ValueError:
                logging.error("  >> Parameter 'to_url' is not a valid URL.")

            retval["task_id"] = task_id
            retval["status"] = SUCCESS

            job = send_webhook(
                webhook_payload={
                    "url": retval["origin"],
                    "auth": user.api_key,
                    "payload": retval
                }
            )

    def on_failure(self, exc, task_id, args, kwargs, info):
        """
        exc – The exception raised by the task.
        task_id – Unique id of the failed task.
        args – Original arguments for the task that failed.
        kwargs – Original keyword arguments for the task that failed.
        """

        # user = mariadb.load_user_by_id(args["user_id"])
        #
        # if user and user.api_key and args["origin"]:
        #     try:
        #         hook.validate_url(args["origin"])
        #     except ValueError:
        #         logging.error("  >> Parameter 'to_url' is not a valid URL.")
        #     job = hook.send_webhook(
        #         webhook_payload={
        #             "url": args["origin"],
        #             "auth": user.api_key,
        #             "payload": args
        #         }
        #     )


@celery.task(base=CallbackTask, name="transcribe", bind=True)
def transcribe(self, received_date, duration, num_channels, user_id, talk_record_id, resampler, unique_uuid, origin):

    results = []
    transcription_date = datetime.now(timezone.utc).isoformat()[:-9]
    try:
        for file_path in resampler:
            logging.info(
                f'  == Request {unique_uuid} transcribing file: {file_path}.'
            )
            transcription = whisper.pipe(os.path.join(variables.file_dir, file_path), return_timestamps=True)
            transcription.pop('text', None)
            results.append(transcription)
    except Exception as e:
        logging.info(
            f'  == Request {unique_uuid} finished with error {e}.'
        )

    return dict(
        received_date=received_date,
        transcription_date=transcription_date,
        start_transcription_date=received_date,
        duration=duration,
        num_channels=num_channels,
        user_id=user_id,
        talk_record_id=talk_record_id,
        transcription=results,
        origin=origin
    )

