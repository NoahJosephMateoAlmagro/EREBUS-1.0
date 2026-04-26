"""
Console redirection utilities for the EREBUS GUI.

This module contains a file-like object used to redirect stdout and stderr
into a thread-safe queue. The GUI consumes this queue safely from the Tkinter
main thread.
"""


class ConsoleRedirector:
    """
    Redirects stdout or stderr messages into a thread-safe queue.

    The GUI periodically reads this queue and writes the messages into the
    console textbox. This avoids updating Tkinter widgets directly from
    background threads.
    """

    def __init__(self, output_queue, stream_name):
        """
        Initializes the redirector.

        Args:
            output_queue: Queue where console messages are stored.
            stream_name: Name of the stream, usually 'stdout' or 'stderr'.
        """
        self.output_queue = output_queue
        self.stream_name = stream_name

    def write(self, message):
        """
        Writes a message into the queue.

        Args:
            message: Text written to stdout or stderr.
        """
        if message:
            self.output_queue.put((self.stream_name, message))

    def flush(self):
        """
        Required for file-like compatibility.
        """
        pass