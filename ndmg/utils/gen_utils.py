# !/usr/bin/env python

"""
ndmg.utils.gen_utils
~~~~~~~~~~~~~~~~~~~~

Contains general utility functions.
"""

# system imports
<<<<<<< HEAD
=======
import warnings

warnings.simplefilter("ignore")
>>>>>>> staging
import os
import os.path as op
import sys
from subprocess import Popen, PIPE
import subprocess

# package imports
import numpy as np
import nibabel as nib
from nilearn.image import mean_img
from scipy.sparse import lil_matrix
from fury import actor
from fury import window

import dipy
from dipy.io import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.align.reslice import reslice

# ndmg imports
from ndmg.utils import reg_utils



def check_exists(*dargs):
    """
    Decorator. For every integer index passed to check_exists, 
    checks if the argument passed to that index in the function decorated contains a filepath that exists.
    Also standardizes print statements across functions.
    
    Parameters
    ----------
    dargs : ints
        Where to check the function being decorated for files.
        
    Raises
    ------
    ValueError
        Raised if the file at that location doesn't exist.
    
    Returns
    -------
    func
        dictionary of output files
    """

    def outer(f):
        def inner(*args, **kwargs):

            for darg in dargs:
                p = args[darg]
                try:
                    if not os.path.exists(p):
                        raise ValueError(
                            f"{p} does not exist.\nThis is an input to the function {f.__name__}."
                        )
                except TypeError:
                    print(
                        f"{darg} is not a file, it is {type(darg)}. \nFix decorator on this function."
                    )

                print(f"{p} exists.")
            print(
                f"Prerequisite files for {f.__name__} all exist. Calling {f.__name__}."
            )
            print("\n")

            return f(*args, **kwargs)

        return inner

    return outer


def check_dependencies():
    """
    Check for the existence of FSL and AFNI.
    Stop the pipeline immediately if these dependencies are not installed.

    Raises
    ------
    AssertionError
        Raised if FSL is not installed.
    AssertionError
        Raised if AFNI is not installed.
    """

    # Check for python version
    print(f"Python location : {sys.executable}")
    print(f"Python version : {sys.version}")
    print(f"DiPy version : {dipy.__version__}")
    if sys.version_info[0] < 3:
        warnings.warn(
            "WARNING : Using python 2. This Python version is no longer maintained. Use at your own risk."
        )

    # Check FSL installation
    try:
        print(f"Your fsl directory is located here: {os.environ['FSLDIR']}")
    except KeyError:
        raise AssertionError(
            "You do not have FSL installed! See installation instructions here: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation"
        )

    # Check AFNI installation
    try:
        print(
            f"Your AFNI directory is located here: {subprocess.check_output('which afni', shell=True, universal_newlines=True)}"
        )
    except subprocess.CalledProcessError:
        raise AssertionError(
            "You do not have AFNI installed! See installation instructions here: https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/background_install/main_toc.html"
        )


def show_template_bundles(final_streamlines, template_path, fname):
    """Displayes the template bundles
    
    Parameters
    ----------
    final_streamlines : list
        Generated streamlines
    template_path : str
        Path to reference FA nii.gz file
    fname : str
        Path of the output file (saved as )
    """

    renderer = window.Renderer()
    template_img_data = nib.load(template_path).get_data().astype("bool")
    template_actor = actor.contour_from_roi(
        template_img_data, color=(50, 50, 50), opacity=0.05
    )
    renderer.add(template_actor)
    lines_actor = actor.streamtube(
        final_streamlines, window.colors.orange, linewidth=0.3
    )
    renderer.add(lines_actor)
    window.record(renderer, n_frames=1, out_path=fname, size=(900, 900))
    return


def execute_cmd(cmd, verb=False):
    """Given a bash command, it is executed and the response piped back to the
    calling script
    
    Parameters
    ----------
    cmd : str
        command you want to execute
    verb : bool, optional
        whether to print the command that is being executed, by default False
    
    Returns
    -------
    stdout
        outputs from p.communicate
    stderr
        error from p.communicate
    """

    if verb:
        print("Executing: {}".format(cmd))

    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate()
    code = p.returncode
    if code:
        sys.exit("Error {}: {}".format(code, err))
    return out, err


def get_braindata(brain_file):
    """Opens a brain data series for a mask, mri image, or atlas.
    Returns a numpy.ndarray representation of a brain.
    
    Parameters
    ----------
    brain_file : str, nibabel.nifti1.nifti1image, numpy.ndarray
        an object to open the data for a brain. Can be a string (path to a brain file),
        nibabel.nifti1.nifti1image, or a numpy.ndarray
    
    Returns
    -------
    array
        array of image data
    
    Raises
    ------
    TypeError
        Brain file is not an accepted format
    """

    if type(brain_file) is np.ndarray:  # if brain passed as matrix
        braindata = brain_file
    else:
        if type(brain_file) is str or type(brain_file) is str:
            brain = nib.load(str(brain_file))
        elif type(brain_file) is nib.nifti1.Nifti1Image:
            brain = brain_file
        else:
            raise TypeError(
                "Brain file is type: {}".format(type(brain_file))
                + "; accepted types are numpy.ndarray, "
                "string, and nibabel.nifti1.Nifti1Image."
            )
        braindata = brain.get_data()
    return braindata


def get_filename(label):
    """Given a fully qualified path, return just the file name, without extension
    
    Parameters
    ----------
    label : str
        Path to file you want isolated
    
    Returns
    -------
    str
        File name
    """
    return os.path.basename(label).split(".")[0]


def get_slice(mri, volid, sli):
    """Takes a volume index and constructs a new nifti image from the specified volume
    
    Parameters
    ----------
    mri : str
        Path to the 4d mri volume you wish to extract a slice from
    volid : int
        The index of the volume desired
    sli : str
        Path for the resulting file containing the desired slice
    """

    mri_im = nib.load(mri)
    data = mri_im.get_data()
    # get the slice at the desired volume
    vol = np.squeeze(data[:, :, :, volid])

    # Wraps volume in new nifti image
    head = mri_im.get_header()
    head.set_data_shape(head.get_data_shape()[0:3])
    out = nib.Nifti1Image(vol, affine=mri_im.get_affine(), header=head)
    out.update_header()
    # and saved to a new file
    nib.save(out, sli)


def make_gtab_and_bmask(fbval, fbvec, dwi_file, outdir):
    """Takes bval and bvec files and produces a structure in dipy format while also using FSL commands
    
    Parameters
    ----------
    fbval : str
        Path to b-value file
    fbvec : str
        Path to b-vector file
    dwi_file : str
        Path to dwi file being analyzed
    outdir : str
        output directory
    
    Returns
    -------
    GradientTable
        gradient table created from bval and bvec files
    str
        location of averaged b0 image file
    str
        location of b0 brain mask file
    """

    # Use B0's from the DWI to create a more stable DWI image for registration
    nodif_B0 = "{}/nodif_B0.nii.gz".format(outdir)
    nodif_B0_bet = "{}/nodif_B0_bet.nii.gz".format(outdir)
    nodif_B0_mask = "{}/nodif_B0_bet_mask.nii.gz".format(outdir)

    # loading bvecs/bvals
    print(fbval)
    print(fbvec)
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)

    # Creating the gradient table
    gtab = gradient_table(bvals, bvecs, atol=1.0)

    # Correct b0 threshold
    gtab.b0_threshold = min(bvals)

    # Get B0 indices
    B0s = np.where(gtab.bvals == gtab.b0_threshold)[0]
    print("%s%s" % ("B0's found at: ", B0s))

    # Show info
    print(gtab.info)

    # Extract and Combine all B0s collected
    print("Extracting B0's...")
    cmds = []
    B0s_bbr = []
    for B0 in B0s:
        print(B0)
        B0_bbr = "{}/{}_B0.nii.gz".format(outdir, str(B0))
        cmd = "fslroi " + dwi_file + " " + B0_bbr + " " + str(B0) + " 1"
        cmds.append(cmd)
        B0s_bbr.append(B0_bbr)

    for cmd in cmds:
        print(cmd)
        os.system(cmd)

    # Get mean B0
    B0s_bbr_imgs = []
    for B0 in B0s_bbr:
        B0s_bbr_imgs.append(nib.load(B0))

    mean_B0 = mean_img(B0s_bbr_imgs)
    nib.save(mean_B0, nodif_B0)

    # Get mean B0 brain mask
    cmd = "bet " + nodif_B0 + " " + nodif_B0_bet + " -m -f 0.2"
    os.system(cmd)
    return gtab, nodif_B0, nodif_B0_mask


def reorient_dwi(dwi_prep, bvecs, namer):
    """Orients dwi data to the proper orientation (RAS+) using nibabel
    
    Parameters
    ----------
    dwi_prep : str
        Path to eddy corrected dwi file
    bvecs : str
        Path to the resaled b-vector file
    namer : NameResource
        NameResource variable containing relevant directory tree information
    
    Returns
    -------
    str
        Path to potentially reoriented dwi file
    str
        Path to b-vector file, potentially reoriented if dwi data was
    """

    fname = dwi_prep
    bvec_fname = bvecs
    out_bvec_fname = "%s%s" % (namer.dirs["output"]["prep_dwi"], "/bvecs_reor.bvec")

    input_img = nib.load(fname)
    input_axcodes = nib.aff2axcodes(input_img.affine)
    reoriented = nib.as_closest_canonical(input_img)
    normalized = reg_utils.normalize_xform(reoriented)
    # Is the input image oriented how we want?
    new_axcodes = ("R", "A", "S")
    if normalized is not input_img:
        out_fname = "%s%s%s%s" % (
            namer.dirs["output"]["prep_dwi"],
            "/",
            dwi_prep.split("/")[-1].split(".nii.gz")[0],
            "_reor_RAS.nii.gz",
        )
        print("%s%s%s" % ("Reorienting ", dwi_prep, " to RAS+..."))

        # Flip the bvecs
        input_orientation = nib.orientations.axcodes2ornt(input_axcodes)
        desired_orientation = nib.orientations.axcodes2ornt(new_axcodes)
        transform_orientation = nib.orientations.ornt_transform(
            input_orientation, desired_orientation
        )
        bvec_array = np.loadtxt(bvec_fname)
        if bvec_array.shape[0] != 3:
            bvec_array = bvec_array.T
        if not bvec_array.shape[0] == transform_orientation.shape[0]:
            raise ValueError("Unrecognized bvec format")
        output_array = np.zeros_like(bvec_array)
        for this_axnum, (axnum, flip) in enumerate(transform_orientation):
            output_array[this_axnum] = bvec_array[int(axnum)] * float(flip)
        np.savetxt(out_bvec_fname, output_array, fmt="%.8f ")
    else:
        out_fname = "%s%s%s%s" % (
            namer.dirs["output"]["prep_dwi"],
            "/",
            dwi_prep.split("/")[-1].split(".nii.gz")[0],
            "_RAS.nii.gz",
        )
        out_bvec_fname = bvec_fname

    normalized.to_filename(out_fname)

    return out_fname, out_bvec_fname


def reorient_img(img, namer):
    """Reorients input image to RAS+
    
    Parameters
    ----------
    img : str
        Path to image being reoriented
    namer : NameResource
        NameResource object containing all revlevent pathing information for the pipeline
    
    Returns
    -------
    str
        Path to reoriented image
    """

    # Load image, orient as RAS
    orig_img = nib.load(img)
    reoriented = nib.as_closest_canonical(orig_img)
    normalized = reg_utils.normalize_xform(reoriented)

    # Image may be reoriented
    if normalized is not orig_img:
        print("%s%s%s" % ("Reorienting ", img, " to RAS+..."))
        out_name = "%s%s%s%s" % (
            namer.dirs["output"]["prep_anat"],
            "/",
            img.split("/")[-1].split(".nii.gz")[0],
            "_reor_RAS.nii.gz",
        )
    else:
        out_name = "%s%s%s%s" % (
            namer.dirs["output"]["prep_anat"],
            "/",
            img.split("/")[-1].split(".nii.gz")[0],
            "_RAS.nii.gz",
        )

    normalized.to_filename(out_name)

    return out_name


def match_target_vox_res(img_file, vox_size, namer, sens):
    """Reslices input MRI file if it does not match the targeted voxel resolution. Can take dwi or t1w scans.
    
    Parameters
    ----------
    img_file : str
        path to file to be resliced
    vox_size : str
        target voxel resolution ('2mm' or '1mm')
    namer : NameResource
        NameResource variable containing relevant directory tree information
    sens : str
        type of data being analyzed ('dwi' or 'func')
    
    Returns
    -------
    str
        location of potentially resliced image
    """

    # Check dimensions
    img = nib.load(img_file)
    data = img.get_fdata()
    affine = img.affine
    hdr = img.header
    zooms = hdr.get_zooms()[:3]
    if vox_size == "1mm":
        new_zooms = (1.0, 1.0, 1.0)
    elif vox_size == "2mm":
        new_zooms = (2.0, 2.0, 2.0)

    if (abs(zooms[0]), abs(zooms[1]), abs(zooms[2])) != new_zooms:
        print("Reslicing image " + img_file + " to " + vox_size + "...")
        if sens == "dwi":
            img_file_res = "%s%s%s%s" % (
                namer.dirs["output"]["prep_dwi"],
                "/",
                os.path.basename(img_file).split(".nii.gz")[0],
                "_res.nii.gz",
            )
        elif sens == "t1w":
            img_file_res = "%s%s%s%s" % (
                namer.dirs["output"]["prep_anat"],
                "/",
                os.path.basename(img_file).split(".nii.gz")[0],
                "_res.nii.gz",
            )

        data2, affine2 = reslice(data, affine, zooms, new_zooms)
        img2 = nib.Nifti1Image(data2, affine=affine2)
        nib.save(img2, img_file_res)
        img_file = img_file_res
    else:
        print("Reslicing image " + img_file + " to " + vox_size + "...")
        if sens == "dwi":
            img_file_nores = "%s%s%s%s" % (
                namer.dirs["output"]["prep_dwi"],
                "/",
                os.path.basename(img_file).split(".nii.gz")[0],
                "_nores.nii.gz",
            )
        elif sens == "t1w":
            img_file_nores = "%s%s%s%s" % (
                namer.dirs["output"]["prep_anat"],
                "/",
                os.path.basename(img_file).split(".nii.gz")[0],
                "_nores.nii.gz",
            )
        nib.save(img, img_file_nores)
        img_file = img_file_nores

    return img_file


<<<<<<< HEAD
=======
def load_timeseries(timeseries_file, ts="roi"):
    """Loads timeseries data. Exists to standardize formatting in case changes are made
    with how timeseries are saved in future versions.
    
    Parameters
    ----------
    timeseries_file : str
        Path to the file you wish to load timeseries data from
    ts : str, optional
        Timeseries type, either 'roi' or 'voxel, by default "roi"
    
    Returns
    -------
    [type]
        [description]
    """

    if (ts == "roi") or (ts == "voxel"):
        timeseries = np.load(timeseries_file)["roi"]
        return timeseries
    else:
        print(
            "You have not selected a valid timeseries type."
            + "options are ts='roi' or ts='voxel'."
        )
    pass


>>>>>>> staging
def parcel_overlap(parcellation1, parcellation2, outpath):
    """A function to compute the percent composition of each parcel in
    parcellation 1 with the parcels in parcellation 2. Rows are indices
    in parcellation 1; cols are parcels in parcellation 2. Values are the
    percent of voxels in parcel (parcellation 1) that fall into parcel
    (parcellation 2). Implied is that each row sums to 1.
    
    Parameters
    ----------
    parcellation1 : str
        the path to the first parcellation.
    parcellation2 : str
        the path to the second parcellation.
    outpath : str
        the path to produce the output.
    """

    p1_dat = nib.load(parcellation1).get_data()
    p2_dat = nib.load(parcellation2).get_data()
    p1regs = np.unique(p1_dat)
    p1regs = p1regs[p1regs > 0]
    p2regs = np.unique(p2_dat)

    p1n = get_filename(parcellation1)
    p2n = get_filename(parcellation2)

    overlapdat = lil_matrix((p1regs.shape[0], p2regs.shape[0]), dtype=np.float32)
    for p1idx, p1reg in enumerate(p1regs):
        p1seq = p1_dat == p1reg
        N = p1seq.sum()
        poss_regs = np.unique(p2_dat[p1seq])
        for p2idx, p2reg in enumerate(p2regs):
            if p2reg in poss_regs:
                # percent overlap is p1seq and'd with the anatomical region voxelspace, summed and normalized
                pover = np.logical_and(p1seq, p2_dat == p2reg).sum() / float(N)
                overlapdat[p1idx, p2idx] = pover

    outf = op.join(outpath, "{}_{}.csv".format(p1n, p2n))
    with open(outf, "w") as f:
        p2str = ["%s" % x for x in p2regs]
        f.write("p1reg," + ",".join(p2str) + "\n")
        for idx, p1reg in enumerate(p1regs):
            datstr = ["%.4f" % x for x in overlapdat[idx,].toarray()[0,]]
            f.write(str(p1reg) + "," + ",".join(datstr) + "\n")
        f.close()
    return
