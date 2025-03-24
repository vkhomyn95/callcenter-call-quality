import logging
import os
from io import BytesIO

import torchaudio
from torchaudio import AudioMetaData

from communicator.variables import variables


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
    def get_save_directory(received_date):
        # Create directory path based on received date (year/month/day)
        year, month, day = received_date.split('T')[0].split("-")
        save_dir = os.path.join(variables.file_dir, year, month, day)

        # Create the directories if they do not exist
        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    def resample(self, info: AudioMetaData, audio: bytes, received_date):
        """Get the name of the current global backend

        :ivar bytes audio: bytes from upload audio

        Returns:
            list or None:
                If upload audio sample rate is less or above 16_000 Hz than make resampling.
                If upload file channels is more than 2 (stereo). Split to mono in separate file.
        """

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

        """ Split channels to separate mono file if upload file is stereo. """
        save_dir = self.get_save_directory(received_date)
        # if info.num_channels > 1:
        #     for channel in range(info.num_channels):
        #         file_path = os.path.join(save_dir, self.unique_uuid + "_" + str(channel) + ".wav")
        #         torchaudio.save(
        #             file_path,
        #             waveform[channel].unsqueeze(0),
        #             sample_rate=self.default_sample_rate,
        #             format=self.default_audio_format
        #         )
        #         files.append(file_path)
        #         logging.info(
        #             f'  == Request {self.unique_uuid} split channel {channel} to mono and saved file as {file_path}.'
        #         )
        # else:
        #     file_path = os.path.join(save_dir, self.unique_uuid + "_" + str(info.num_channels) + ".wav")
        #     torchaudio.save(
        #         file_path,
        #         waveform,
        #         sample_rate=self.default_sample_rate,
        #         format=self.default_audio_format
        #     )
        #     files.append(file_path)
        #     logging.info(
        #         f'  == Request {self.unique_uuid} saved file as {file_path}.'
        #     )
        file_path = os.path.join(save_dir, self.unique_uuid + "_" + str(info.num_channels) + ".wav")
        torchaudio.save(
            file_path,
            waveform,
            sample_rate=self.default_sample_rate,
            format=self.default_audio_format
        )
        files.append(file_path)
        logging.info(
            f'  == Request {self.unique_uuid} saved file as {file_path}.'
        )
        return files
