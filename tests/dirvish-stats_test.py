#!/usr/bin/python
'''Unittests for dirvish-stats'''

import dirvish_stats as ds
import unittest
import os

class ExternalAction(unittest.TestCase):
    def testInitDB(self):
        pass

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
        self.assertEqual(self.teststring_, ds.multi_open(filename).readlines()[0])
    def testGzip(self):
        self.multi_open(self.wd('gz/foo'))
        self.multi_open(self.wd('gzip/foo'))
    def testBzip2(self):
        self.multi_open(self.wd('bz2/foo'))
        self.multi_open(self.wd('bzip2/foo'))
    def testPlain(self):
        self.multi_open(self.wd('plain/foo'))
    def testFileNotFound(self):
        self.assertRaises(RuntimeError, self.multi_open, self.wd('nonexistent'))

if __name__ == '__main__':
    unittest.main()
