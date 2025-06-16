import logging
from io import BytesIO

import torchaudio
from torchaudio import AudioMetaData

from communicator.variables import variables

from communicator.database.minio_client import minio_client


class Resampler:
    """Resampler()

    :ivar str unique_uuid: unique identifier for request
    Return manipulation with upload file.

    """

    def __init__(self, unique_uuid):
        torchaudio.set_audio_backend("sox_io")
        self.unique_uuid = unique_uuid
        self.default_sample_rate = 16_000
        self.default_resampling_method = "sinc_interpolation"
        self.default_audio_format = "wav"

    @staticmethod
    def _get_object_name_prefix(received_date: str) -> str:
        year, month, day = received_date.split('T')[0].split("-")
        return f"{year}/{month}/{day}"

    def resample(self, info: AudioMetaData, audio: bytes, received_date):
        """Get the name of the current global backend

        :ivar bytes audio: bytes from upload audio

        Returns:
            list or None:
                If upload audio sample rate is less or above 16_000 Hz than make resampling.
                If upload file channels is more than 2 (stereo). Split to mono in separate file.
        """

        if not minio_client:
            logging.error(f"  == Request {self.unique_uuid} пропущено: клієнт MinIO не ініціалізований.")
            return []

        files: list = []
        waveform, sample_rate = torchaudio.load(BytesIO(audio))

        if info.sample_rate != self.default_sample_rate:
            logging.info(
                f'  == Request {self.unique_uuid} '
                f'resampling file from {info.sample_rate} to {self.default_sample_rate}.'
            )
            """ Resample upload file to 16_000 Hz. """
            waveform = torchaudio.transforms.Resample(
                sample_rate,
                self.default_sample_rate,
                resampling_method=self.default_resampling_method
            )(waveform)

        object_name_prefix = self._get_object_name_prefix(received_date)
        object_name = f"{object_name_prefix}/{self.unique_uuid}.{self.default_audio_format}"

        buffer = BytesIO()
        torchaudio.save(
            buffer,
            waveform,
            sample_rate=self.default_sample_rate,
            format=self.default_audio_format
        )
        buffer_size = buffer.getbuffer().nbytes
        buffer.seek(0)

        try:
            minio_client.put_object(
                bucket_name=variables.minio_bucket,
                object_name=object_name,
                data=buffer,
                length=buffer_size,
                content_type='audio/wav'
            )
            files.append(object_name)
            logging.info(
                f'  == Request {self.unique_uuid} stored to MinIO as: {object_name}'
            )
        except Exception as e:
            logging.error(
                f'  == Request {self.unique_uuid} can not store to MinIO: {e}'
            )

        return files
