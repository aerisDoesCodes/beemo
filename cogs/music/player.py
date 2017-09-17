import shlex
import discord.voice_client as voice_client
import threading
import subprocess
import traceback

class StreamPlayer(voice_client.StreamPlayer):
    def __init__(self, stream, encoder, connected, player, after, **kwargs):
        self.buff = stream
        self.frame_size = encoder.frame_size
        self.player = player
        self._end = threading.Event()
        self._resumed = threading.Event()
        self._resumed.set() # we are not paused
        self._connected = connected
        self.after = after
        self.delay = encoder.frame_length / 1000.0
        self._volume = 1.0
        self._current_error = None

class ProcessPlayer(StreamPlayer):
    def __init__(self, process, client, after, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self.daemon = True
        self.process = process
        self.client = client
        self.after = after
        self.kwargs = kwargs

    def run(self):
        try:
            self.process = self.process()
        except:
            traceback.print_exc()
            return
        StreamPlayer.__init__(self, self.process.stdout, self.client.encoder,
                         self.client._connected, self.client.play_audio, self.after, **self.kwargs)
        StreamPlayer.run(self)

        self.process.kill()
        if self.process.poll() is None:
            self.process.communicate()


def create_ffmpeg_player(self, filename, *, use_avconv=False, pipe=False, stderr=None, options=None, before_options=None, headers=None, after=None):
    command = 'ffmpeg' if not use_avconv else 'avconv'
    input_name = '-' if pipe else shlex.quote(filename)
    before_args = ""
    if isinstance(headers, dict):
        for key, value in headers.items():
            before_args += "{}: {}\r\n".format(key, value)
        before_args = ' -headers ' + shlex.quote(before_args)

    if isinstance(before_options, str):
        before_args += ' ' + before_options

    cmd = command + '{} -i {} -f s16le -ar {} -ac {} -loglevel warning'
    cmd = cmd.format(before_args, input_name, self.encoder.sampling_rate, self.encoder.channels)

    if isinstance(options, str):
        cmd = cmd + ' ' + options

    cmd += ' pipe:1'

    stdin = None if not pipe else filename
    args = shlex.split(cmd)
    #try:
    p = lambda: subprocess.Popen(args, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr)
    return ProcessPlayer(p, self, after)
    # except FileNotFoundError as e:
    #     raise ClientException('ffmpeg/avconv was not found in your PATH environment variable') from e
    # except subprocess.SubprocessError as e:
    #     raise ClientException('Popen failed: {0.__name__} {1}'.format(type(e), str(e))) from e