# /system/core/mkbootimg/mkbootimg  pack script in Android sourch code
# /system/core/mkbootimg/bootimg.h  boot.img struct

'''
#define BOOT_MAGIC "ANDROID!"
#define BOOT_MAGIC_SIZE 8
#define BOOT_NAME_SIZE 16
#define BOOT_ARGS_SIZE 512
#define BOOT_EXTRA_ARGS_SIZE 1024

struct boot_img_hdr
{
    uint8_t magic[BOOT_MAGIC_SIZE];

    uint32_t kernel_size;  /* size in bytes */
    uint32_t kernel_addr;  /* physical load addr */

    uint32_t ramdisk_size; /* size in bytes */
    uint32_t ramdisk_addr; /* physical load addr */

    uint32_t second_size;  /* size in bytes */
    uint32_t second_addr;  /* physical load addr */

    uint32_t tags_addr;    /* physical addr for kernel tags */
    uint32_t page_size;    /* flash page size we assume */
    uint32_t unused;       /* reserved for future expansion: MUST be 0 */

    /* operating system version and security patch level; for
     * version "A.B.C" and patch level "Y-M-D":
     * ver = A << 14 | B << 7 | C         (7 bits for each of A, B, C)
     * lvl = ((Y - 2000) & 127) << 4 | M  (7 bits for Y, 4 bits for M)
     * os_version = ver << 11 | lvl */
    uint32_t os_version;

    uint8_t name[BOOT_NAME_SIZE]; /* asciiz product name */

    uint8_t cmdline[BOOT_ARGS_SIZE];

    uint32_t id[8]; /* timestamp / checksum / sha1 / etc */

    /* Supplemental command line data; kept here to maintain
     * binary compatibility with older versions of mkbootimg */
    uint8_t extra_cmdline[BOOT_EXTRA_ARGS_SIZE];
} __attribute__((packed));

/*
** +-----------------+
** | boot header     | 1 page
** +-----------------+
** | kernel          | n pages
** +-----------------+
** | ramdisk         | m pages
** +-----------------+
** | second stage    | o pages
** +-----------------+
**
** n = (kernel_size + page_size - 1) / page_size
** m = (ramdisk_size + page_size - 1) / page_size
** o = (second_size + page_size - 1) / page_size
**
** 0. all entities are page_size aligned in flash
** 1. kernel and ramdisk are required (size != 0)
** 2. second is optional (second_size == 0 -> no second)
** 3. load each element (kernel, ramdisk, second) at
**    the specified physical address (kernel_addr, etc)
** 4. prepare tags at tag_addr.  kernel_args[] is
**    appended to the kernel commandline in the tags.
** 5. r0 = 0, r1 = MACHINE_TYPE, r2 = tags_addr
** 6. if second_size != 0: jump to second_addr
**    else: jump to kernel_addr
*/




'''



import os
import sys
import struct
import math
import gzip
import shutil


def adjustpage(offset):
    if (offset) % 4096:
        adjustoffset = (((offset) / 4096) + 1) * 4096
    else:
        adjustoffset = (((offset) / 4096) + 1) * 4096




class Boothead():
    def __init__(self):
        self.MAGICNUM = ''
        self.kernel_size = 0
        self.kernel_addr = 0
        self.ramdisk_size = 0
        self.ramdisk_addr = 0
        self.second_size = 0
        self.second_addr = 0
        self.tags_addr = 0
        self.page_size = 0
        self.unused = 0
        self.os_version = 0
        self.name = ''
        self.cmdline = ''
        self.id = 0
        self.extra_cmdline = ''


class ImgExtractor():
    def __init__(self, imgpath,output_dir):
        self.imgpath = imgpath
        self.outputdir = output_dir
        self.imgdata = open(self.imgpath, 'rb').read()
        self.imghead = Boothead()
        self.pageshift = 12

    def getimghead(self):
        self.imghead.MAGICNUM = self.imgdata[0:8]
        self.imghead.kernel_size,\
        self.imghead.kernel_addr,\
        self.imghead.ramdisk_size,\
        self.imghead.ramdisk_addr,\
        self.imghead.second_size,\
        self.imghead.ramdisk_addr,\
        self.imghead.tags_addr,\
        self.imghead.page_size,\
        self.imghead.unused,\
        self.imghead.os_version = struct.unpack_from('10I', self.imgdata, 8)
        self.imghead.name,self.imghead.cmdline = struct.unpack_from('16s512s',self.imgdata,48)
        self.imghead.id =  struct.unpack_from("32s",self.imgdata,576)[0].encode('hex')[:40]
        self.imghead.extra_cmdline = struct.unpack_from('1024s',self.imgdata,608)


    def Extractkernel(self):
        self.getimghead()
        if self.imghead.MAGICNUM != "ANDROID!":
            print "not a bootimg"
            return


        kernelend = self.imghead.page_size+self.imghead.kernel_size
        kernel = self.imgdata[self.imghead.page_size:kernelend]

        #1.maybe the kernel is compressed and contain self decompress code
        #2.kernel  maybe pad with dtb file 

        #compressed kernel  (AKA  Image.gz )

        if struct.unpack_from(">I",kernel,0)[0] == 0x1f8b0800:
            f = open(os.path.join(self.outputdir,'Image_gz'),'wb')
            f.write(kernel)
            f.close
            shutil.copy(os.path.join(self.outputdir,'Image_gz'),os.path.join(self.outputdir,'Image.gz'))
            os.system('gzip -d -f %s'  %   os.path.join(self.outputdir,'Image.gz'))
            #g = gzip.GzipFile('rb', fileobj=open(os.path.join(self.outputdir,'Image'), 'rb'))
            #g.read()
            #open(os.path.join(self.outputdir,'Imagetest'),'wb').write(g.read())

        # self-decompress kernel (AKA zImage)
        elif kernel.startswith("0000A0E10000A0E10000A0E10000A0E10000A0E10000A0E10000A0E10000A0E1".decode('hex')):
            print 'get compress'
            f = open(os.path.join(self.outputdir, 'zImage'), 'wb')
            f.write(kernel)
            f.close
            kerneloff = kernel.find("1F8B0800".decode('hex'))

            f = open(os.path.join(self.outputdir, 'Image_gz'), 'wb')
            f.write(kernel[kerneloff:])
            f.close

            shutil.copy(os.path.join(self.outputdir, 'Image_gz'), os.path.join(self.outputdir, 'Image.gz'))
            os.system('gzip -d -fq %s' % os.path.join(self.outputdir, 'Image.gz'))
        # orignal kernel (Image)
        else:
            f = open(os.path.join(self.outputdir, 'Image_gz'), 'wb')
            f.write(kernel)
            f.close













        self.pageshift=int(math.log(self.imghead.page_size,2))


        #adjust offset
        ramdiskstart = ((kernelend>>self.pageshift)<<self.pageshift)+self.imghead.page_size

        ramdiskend = ramdiskstart+self.imghead.ramdisk_size
        ramdisk = self.imgdata[ramdiskstart:ramdiskend]


        #maybe compressed not handle yet
        f = open(os.path.join(self.outputdir,'ramdisk.img'),'wb')
        f.write(ramdisk)

        '''second stage 
        
        secondstagestart = ((ramdiskend>>self.pageshift)<<self.pageshift)+self.imghead.page_size
        f = open(os.path.join(self.outputdir, 'secondstage'), 'wb')
        
        '''








if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: python ImageExtractor.py  bootimg_path  output_dir"
        exit(0)
    if os.path.exists(sys.argv[1]) != True:
        print "can not find img file"
        exit(0)
    if os.path.isdir(sys.argv[2]) != True:
        print "output dir is not ready"
        exit(0)
    imgextractor = ImgExtractor(sys.argv[1],sys.argv[2])
    imgextractor.Extractkernel()

