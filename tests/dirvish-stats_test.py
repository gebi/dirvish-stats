#!/usr/bin/python
'''Unittests for dirvish-stats'''

import dirvish_stats as ds
import unittest
import os
import tempfile
import subprocess
import StringIO

BIN_='./dirvish_stats.py'
DBTYPES="gdbm tch tcb".split()

class ParseIndex(unittest.TestCase):
    def _parse(self, line):
        strio = StringIO.StringIO(line)
        strio.name='StringIOFile'
        strio.seek(0)
        return list(ds.parse_index(strio))
    def testFile(self):
        line = '123 0 -rwxrwxrwx 1 user group 1000 May 13 14:27 filename\n'
        linew= '123 0 -rwxrwxrwx 1 user group 1000 May 13 14:27 file name\n'
        for i in [line, linew]:
            out = self._parse(i)
            self.assertEqual(('123', '-', 1000, i), out[0])
    def testDirectory(self):
        line = '123 0 drwxrwxrwx 1 user group 1000 May 13 14:27 filename\n'
        out = self._parse(line)
        self.assertEqual(('123', 'd', 1000, line), out[0])
    def testDevCharLinux(self):
        line = '123 0 crwxrwxrwx 1 user group      May 13 14:27 filename\n'
        linew= '123 0 crwxrwxrwx 1 user group      May 13 14:27 file name\n'
        for i in [line, linew]:
            out = self._parse(i)
            self.assertEqual(len(out), 0)
    def testDevBlockLinux(self):
        line = '123 0 brwxrwxrwx 1 user group      May 13 14:27 filename\n'
        linew= '123 0 brwxrwxrwx 1 user group      May 13 14:27 file name\n'
        for i in [line, linew]:
            out = self._parse(i)
            self.assertEqual(len(out), 0)
    def testDevCharBSD(self):
        line = '123 0 crwxrwxrwx 1 user group 3, 2 May 13 14:27 filename\n'
        linew= '123 0 crwxrwxrwx 1 user group 3, 2 May 13 14:27 file name\n'
        for i in [line, linew]:
            out = self._parse(i)
            self.assertEqual(len(out), 0)
    def testDevBlockBSD(self):
        line = '123 0 brwxrwxrwx 1 user group 0, 2 May 13 14:27 filename\n'
        linew= '123 0 brwxrwxrwx 1 user group 0, 2 May 13 14:27 file name\n'
        for i in [line, linew]:
            out = self._parse(i)
            self.assertEqual(len(out), 0)
    def testTryDev(self):
        (out, err) = subprocess.Popen('find /dev -ls'.split(), stdout=subprocess.PIPE,
                                                               stderr=subprocess.PIPE).communicate()
        test = self._parse(out)
        self.assertTrue(len(test) > 1)
    def testInvalid(self):
        self.assertRaises(IndexError, self._parse, '123 invalid')
        self.assertRaises(ds.ParsingError, self._parse, '123 0 -rwxrwxrwx 1 user group SIZE_ERROR May 13 14:27 filename')

class Cleaner(object):
    def __init__(self, file=None):
        self.file_ = file
    def add(self, file):
        if self.file_ != None:
            assert(self.file_ == file)
        self.file_ = file
    def cleanup(self):
        if self.file_ != None:
            os.remove(self.file_)
    def str(self):
        return self.file_

class BlackBox(unittest.TestCase):
    def setUp(self):
        try:
            if os.path.isdir(self.tmp_):
                shutil.rmtree(self.tmp_)
        except AttributeError:
            pass
        self.tmp_ = tempfile.mkdtemp(prefix='dirvish-stats_test_')
        self.dbname_ = self._wd('external_action.gdbm')
    def tearDown(self):
        os.rmdir(self.tmp_)

    def _wd(self, filename):
        return ds.path_join(self.tmp_, filename)
    def _line(self, spec):
        '''123 0 -rwxrwxrwx 1 user group 1000 May 13 14:27 filename'''
        (inode, type, size) = spec.split()
        ret = "%d 0 %srwxrwxrwx 1 user group %d May 13 14:27 filename" %(int(inode), type, int(size))
        return ret
    def _createspec(self, specname, spec=None, lines=None):
        if lines == None:
            data = '\n'.join([ self._line(i) for i in spec ])
        else:
            data = '\n'.join(lines)
        specfile = open(self._wd(specname), 'a')
        specfile.write(data)
        specfile.close()
        return specfile.name
    def _createdb(self, spec, action='init'):
        dbname = self.dbname_
        cmd = [BIN_, '-f', dbname, action, spec]
        (out, err) = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE).communicate()
        #print err
        self.assertEqual(err, '')
        return dbname
    def _dumpdb(self, dbname):
        (out, err) = subprocess.Popen([BIN_, 'dump', '-f', dbname], stdout=subprocess.PIPE,
                                                                    stderr=subprocess.PIPE).communicate()
        #assert(err, '')
        self.assertEqual(err, '')
        ret = {}
        for i in out.split('\n'):
            line = i.rstrip()
            if line == "":
                continue
            (inode, refcnt) = line.split()
            ret[int(inode)] = int(refcnt)
        return ret
    def _rmdb(self, dbname):
        if dbname is None:
            return
        os.remove(dbname)
        for i in open(dbname+'.i'):
            file = i.rstrip()
            assert file.startswith(self.tmp_)
            os.remove(file)
        os.remove(dbname+'.i')
    def for_all_dbtypes(self, method):
        dbnames = [ self._wd("external_action."+i) for i in DBTYPES ]
        dbresults = []
        for dbname in dbnames:
            self.dbname_ = dbname
            try:
                method()
            finally:
                dbresults.append(self._dumpdb(dbname))
                self._rmdb(self.dbname_)
        #crosscheck dbs
        numresults = len(dbresults[0])
        for i in dbresults[1:]:
            self.assertEqual(numresults, len(i))
        ref = dbresults[0]
        for db in dbresults[1:]:
            for (k,v) in db.items():
                self.assertEqual(ref[k], v)

    def testInitDB(self):
        def doit():
            spec = self._createspec('1', ["123 - 1248", "123 - 4182", "1234 - 111"])
            dbname = self._createdb(spec)
            ret = self._dumpdb(dbname)
            self.assertEqual(ret[123], 2)
            self.assertEqual(ret[1234], 1)
        self.for_all_dbtypes(doit)
    def testAdd(self):
        def doit():
            spec1 = self._createspec('1', ["123 - 1248"])
            spec2 = self._createspec('2', ["123 - 4182"])
            dbname = self._createdb(spec1)
            dbname = self._createdb(spec2, action='add')
            ret = self._dumpdb(dbname)
            self.assertEqual(ret[123], 2)
        self.for_all_dbtypes(doit)
    def testEmptyDB(self):
        def doit():
            spec = self._createspec('1', ["1234 - 111"])
            dbname = self._createdb(spec)
            dbname = self._createdb(spec, action="rm")
            ret = self._dumpdb(dbname)
            self.assertEqual(ret.has_key(1234), False)
            os.remove(spec)
        self.for_all_dbtypes(doit)
    def testAddDirectory(self):
        def doit():
            spec = self._createspec('1', ["1234 d 111"])
            dbname = self._createdb(spec)
            ret = self._dumpdb(dbname)
            self.assertEqual(ret.has_key(1234), False)
        self.for_all_dbtypes(doit)
    def testRemove(self):
        def doit():
            cleanup_spec2 = Cleaner()
            try:
                spec1 = self._createspec('1', ["123 - 111"])
                spec2 = self._createspec('2', ["1234 - 111"])
                # add + check
                dbname = self._createdb(spec1)
                dbname = self._createdb(spec2, action='add')
                ret = self._dumpdb(dbname)
                self.assertEqual(ret[1234], 1)
                # remove + check
                cleanup_spec2.add(spec2)
                dbname = self._createdb(spec2, action='rm')
                ret = self._dumpdb(dbname)
                self.assertEqual(ret[123], 1)
                self.assertEqual(ret.has_key(1234), False)
            finally:
                cleanup_spec2.cleanup()
        self.for_all_dbtypes(doit)
    def testDoubleAdd(self):
        def doit():
            spec1 = self._createspec('1', ["123 - 1248"])
            spec2 = self._createspec('2', ["1234 - 1248"])
            dbname = self._createdb(spec1)
            dbname = self._createdb(spec2, action='add')
            self.assertRaises(AssertionError, self._createdb, spec1, action='add')
            ret = self._dumpdb(dbname)
            self.assertEqual(ret[123], 1)
            self.assertEqual(ret[1234], 1)
        self.for_all_dbtypes(doit)
    def testDoubleRemove(self):
        def doit():
            cleanup_spec2 = Cleaner()
            try:
                spec1 = self._createspec('1', ["123 - 1248"])
                spec2 = self._createspec('2', ["1234 - 1248"])
                dbname = self._createdb(spec1)
                dbname = self._createdb(spec2, action='add')
                cleanup_spec2.add(spec2)
                dbname = self._createdb(spec2, action='rm')
                self.assertRaises(AssertionError, self._createdb, spec2, action='rm')
                ret = self._dumpdb(dbname)
                self.assertEqual(ret[123], 1)
            finally:
                cleanup_spec2.cleanup()
        self.for_all_dbtypes(doit)
    def testIncDecCornerCase(self):
        def doit():
            cleanup_spec2 = Cleaner()
            try:
                spec1 = self._createspec('1', ["123 - 1248"])
                spec2 = self._createspec('2', ["123 - 1248"])
                dbname = self._createdb(spec1)
                dbname = self._createdb(spec2, action='add')
                ret = self._dumpdb(dbname)
                self.assertEqual(ret[123], 2)
                dbname = self._createdb(spec1, action='rm')
                ret = self._dumpdb(dbname)
                self.assertEqual(ret[123], 1)
                dbname = self._createdb(spec2, action='rm')
                cleanup_spec2.add(spec2)
                ret = self._dumpdb(dbname)
                self.assertEqual(ret.has_key(123), False)
                dbname = self._createdb(spec1, action='add')
                ret = self._dumpdb(dbname)
                self.assertEqual(ret[123], 1)
            finally:
                cleanup_spec2.cleanup()
        self.for_all_dbtypes(doit)
    def testInvalid(self):
        def doit():
            cleanup_spec = Cleaner()
            try:
                speclines = ['123 0 -rwxrwxrwx 1 user group SIZE_ERROR May 13 14:27 filename']
                spec = self._createspec('1', lines=speclines)
                cleanup_spec.add(spec)
                dbname = self.dbname_
                cmd = [BIN_, '-f', dbname, 'init', spec]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                (out, err) = process.communicate()
                self.assertEqual(process.returncode, 1)
            finally:
                cleanup_spec.cleanup()
        self.for_all_dbtypes(doit)

class HumanSizes(unittest.TestCase):
    def testFirstCornerCase(self):
        teststring  = "0 999 1000 1001 1023 1024 1025".split()
        resultstring= "0 999 1000 1001 1023 1.0K 1.0K".split()
        for i,s in zip(teststring, resultstring):
            self.assertEqual(s, ds.human_sizes(int(i)))
    def testUnitsSmall(self):
        base = 1024
        i = 1
        for s in "1.0K 1.0M 1.0G 1.0T 1.0P 1.0E 1.0Z 1.0Y".split():
            self.assertEqual(s, ds.human_sizes(base**i+1))
            i +=1
    def testUnitsBig(self):
        base = 1024
        i = 1
        for s in "11K 11M 11G 11T 11P 11E 11Z 11Y".split():
            self.assertEqual(s, ds.human_sizes(base**i+(base**i*10)))
            i +=1

class MultiOpen(unittest.TestCase):
    teststring_='test\n'
    def wd(self, path):
        return os.path.join('multi_open', path)
    def multi_open(self, filename):
        self.assertEqual(self.teststring_, ds.multi_open(self.wd(filename)).readlines()[0])
    def testGzip(self):
        self.multi_open('gz/foo.gz')
        self.multi_open('gzip/foo.gzip')
    def testBzip2(self):
        self.multi_open('bz2/foo.bz2')
        self.multi_open('bzip2/foo.bzip2')
    def testPlain(self):
        self.multi_open('plain/foo')
    def testFileNotFound(self):
        self.assertRaises(IOError, self.multi_open, 'nonexistent')

if __name__ == '__main__':
    dbtypes = os.getenv('DBTYPES')
    if dbtypes != None:
        DBTYPES=dbtypes.split()
        if len(DBTYPES) == 0:
            DBTYPES=['gdbm']
    print "Running unittests for the following database backends:", ', '.join(DBTYPES)
    unittest.main()
