#!/usr/bin/python

# Author: Disa Mhembere
# Calculate some graph invariants on big and small graphs
# Date: 5 Sept 2012

import os
import argparse
import unittesting

# Invariant imports
from getBaseName import getBaseName
from loadAdjMatrix import loadAdjMat
from maxavgdeg import getMaxAveDegree
from scanstat_degr import calcScanStat_Degree
from triCount import eignTriangleLocal
from clustCoeff import calcLocalClustCoeff
from loadAdjMatrix import loadAdjMat
  
def realgraph(G_fn, lcc_fn, toDir, roiRootName = None):
  
  G = loadAdjMat(G_fn, lcc_fn, roiRootName) # load up graph into main mem
  
  
  MADdir, eigvDir, ssDir, degDir, triDir, ccDir = createInvDirs(toDir)
  eignTriangleLocal(G_fn, G, lcc_fn, roiRootName, triDir, None)
  mad = getMaxAveDegree(G_fn, G, lcc_fn, roiRootName, MADdir, eigvDir, True)
  ss1_fn, deg_fn, numNodes = calcScanStat_Degree(G_fn, G, lcc_fn, roiRootName, ssDir, degDir)
  ccArr_fn = calcLocalClustCoeff(deg_fn, tri_fn, None, None, ccDir, False)
  
#************************#
# Create Invariate Dirs  #
#************************#

def createInvDirs(toDir):
  #Maximum Avearage Degree
  MADdir = os.path.join(toDir, "MAD")
  if not os.path.exists(MADdir):
    os.makedirs(MADdir)
  
  # Eigenvalues 
  eigvDir = os.path.join(toDir, "Eigen")
  if not os.path.exists(eigvDir):
    os.makedirs(eigvDir)
  
  # Scan statistic 
  ssDir = os.path.join(toDir, "ScanStat")
  if not os.path.exists(ssDir):
    os.makedirs(ssDir)
  
  # Degree
  degDir = os.path.join(toDir, "Degree")
  if not os.path.exists(degDir):
    os.makedirs(degDir)
  
  # Triangle count
  triDir = os.path.join(toDir, "Triangle")
  if not os.path.exists(triDir):
    os.makedirs(triDir)
  
  # Clustering Coeff
  ccDir = os.path.join(toDir, "ClustCoeff")
  if not os.path.exists(ccDir):
    os.makedirs(ccDir)
  
  return [ MADdir, eigvDir, ssDir, degDir, triDir, ccDir ]
  

#*********************#
# Printing Functions  #
#*********************#
def printVertInv(fn, invariantName):
  '''
  fn - Invariant full filename
  invariantName - String describing the invariant 
  Print the Scan statistic 1
  '''
  try:
    inv = np.load(fn)
  except:
    print 'Invalid file name: %s' % fn
    sys.exit(-1)

  print '\n%s\n=======================\n' % (invariantName)
  for idx, vert in enumerate (inv):
    print 'Vertex: %d, Value: %d' % (idx, vert)
  
def main():
  
  parser = argparse.ArgumentParser(description='Runs all invariants of the largest connected component of real graphs')
  parser.add_argument('G_fn', action='store',help='Full filename sparse graph (.mat)')
  parser.add_argument('lcc_fn', action='store',help='Full filename of largest connected component (.npy)')
  parser.add_argument('toDir', action='store', help='Full path of directory where you want .npy array resulting files to go')
  parser.add_argument('roiRootName', action='store',help='Full path of roi director + baseName')
  
  result = parser.parse_args()
  
  realgraph(result.G_fn, result.lcc_fn, result.toDir, result.roiRootName)

if __name__ == '__main__':
  main()
