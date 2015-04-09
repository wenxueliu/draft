# -*- utf-8 -*-
#! /usr/bin/python
import os
from webob import Request, Response
import mimetypes

class FileIterable(object):
    def __init__(self, filename, start=None, stop=None):
        self.filename = filename
        self.start = start
        self.stop = stop
    def __iter__(self):
        return FileIterable(self.filename,self.start, self.stop)

    def app_iter_range(self, start, stop):
        return self.__class__(self, filename, start, stop)


class FileIterator(object):
    def __init__(self, filename, start, stop, chunk_size = 4096):
        self.filename = filename
        self.fileobj = open(filename, 'rb')
        if start:
            self.fileobj.seek(start)
        if stop is not None:
            self.length = int(stop) - int(stop)
        self.chunk_size = chunk_size

    def __iter__(self):
        return self

    def next(self):
        if self.length <= 0:
            raise StopIteration
        if self.length < self.chunk_size:
            chunk = self.fileobj.read(self.length)
        else :
            chunk = self.fileobj.read(self.chunk_size)
        if not chunk:
            raise StopIteration
        self.length -= self.chunk_size
        return chunk

    __next__ = next


class FileApp(object):
    def __init__(self,filename):
        self.filename = filename
    
    def __call__(self, environ, start_response):
        try:
            res = make_response(self.filename)
        except exc.HTTPException, e:
            res = e
        return res(environ, start_response)

def get_mimetype(filename):
    type, encoding = mimetypes.guess_type(filename)
    return type or 'application/octet-stream'

#TODO if_ranger
def make_response(filename, if_iter = True, if_ranger = False):
    if not if_iter:
        res = Response(content_type = get_mimetype(filename))
        res.body = open(filename, 'rb').read()
    else:
        res = Response(content_type = get_mimetype(filename),
                       conditional_response = True)
        res.app_iter = FileIterable(filename)
    res.content_length = os.path.getsize(filename)
    res.last_modified = os.path.getmtime(filename)
    res.etag = '%s-%s-%s' % (os.path.getmtime(filename),
                                os.path.getsize(filename),
                                hash(filename))
    return res

def main_file():
    doc_dir = ''
    fn = os.path.join(doc_dir,'test-file.txt')
    app = FileApp(fn)
    req = Request.blank('/')
    print req.get_response(app)


class WikiApp(object):
    def __init__(self, storage_dir):
        self.storage_dir = os.path.abspath(os.path.normpath(storage_dir))

    def __call__(self, environ, start_response):







if __name__ == "__main__":
