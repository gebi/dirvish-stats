#!/usr/bin/python
'''Unittests for dirvish-stats'''

import dirvish_stats as ds
import unittest

class HumanSizes(unittest.TestCase):
    def testFirstCornerCase(self):
        teststring  = "0 999 1000 1001 1024 1025 1026".split()
        resultstring= "0 999 1000 1001 1024 1.0K 1.0K".split()
        for i,s in zip(teststring, resultstring):
            self.assertEqual(s, ds.human_sizes(int(i)))
    def testUnitsSmall(self):
        base = 1024
        i = 1
        for s in "1.0K 1.0M 1.0G 1.0T 1.0P".split():
            self.assertEqual(s, ds.human_sizes(base**i+1))
            i +=1
    def testUnitsBig(self):
        base = 1024
        i = 1
        for s in "11K 11M 11G 11T 11P".split():
            self.assertEqual(s, ds.human_sizes(base**i+(base**i*10)))
            i +=1

if __name__ == '__main__':
    unittest.main()
