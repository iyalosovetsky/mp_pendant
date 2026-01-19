import sys, select 
class TermReader:

  def __init__(self, byte_stream, buffer_bytes=100):
    self.stream, self.poller = byte_stream, select.poll()
    self.rb, self.rb_n, self.rb_len = bytearray(buffer_bytes), 0, buffer_bytes
    self.poller.register(self.stream, select.POLLIN)

  def rb_decode(self, a, b, max_char_len=6):
    'Returns decoded ring-buffer contents from a to b, and a-offset for next call'
    buff = self.rb[a:b] if a < b else self.rb[a:] + self.rb[:b]
    for n in range(max_char_len):
      try: result = buff[:-n or len(buff)].decode()
      except UnicodeError: pass
      else: return result, (self.rb_len + (b - n)) % self.rb_len
    else:
      if len(buff) > max_char_len: raise UnicodeError('Non-UTF-8 stream data')
    return '', a

  def read(self):
    n0, text = self.rb_n, list()
    poll_err = select.POLLHUP | select.POLLERR
    while ev := self.poller.poll(0):
      if ev[0][1] & poll_err or not (byte := self.stream.read(1)): break
      self.rb[self.rb_n] = byte[0]
      self.rb_n = (self.rb_n + 1) % self.rb_len
      if self.rb_n == n0:
        chunk, n0 = self.rb_decode(n0, self.rb_n)
        text.append(chunk)
    if self.rb_n != n0:
      chunk, self.rb_n = self.rb_decode(n0, self.rb_n)
      text.append(chunk)
    return ''.join(text)