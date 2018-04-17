#!/usr/bin/env python
from __future__ import print_function
import rospy
from geometry_msgs.msg import PointStamped
from sensor_msgs.msg import Image
from cv2 import imread # opencv
from os.path import join
from click import progressbar
from cv_bridge import CvBridge, CvBridgeError

def nc_publisher(vo_fn="", im_dir="", rate=1.0):
	rospy.init_node('nc_publisher', anonymous=True)
	rate = rospy.Rate(20.0 * rate) # 20 * rate hz

	if vo_fn != "":
		point_pub = rospy.Publisher('/newcollege/position', PointStamped, queue_size=100)
	if im_dir != "":
		imL_pub = rospy.Publisher('/newcollege/stereo/left', Image, queue_size=10)
		imR_pub = rospy.Publisher('/newcollege/stereo/right', Image, queue_size=10)
		
	cvb = CvBridge()

	with open(vo_fn, 'r') as vo_f:
		with progressbar(vo_f.readlines(), label="Publishing New College Data") as bar:
			for line in bar:
				if not rospy.is_shutdown():
					if len(line) != 0 and line[0] != "#": # skip comments and empty line at the end
						line_split = line.split()
						frame_id = line_split[0]
						t_str = line_split[1] # Need string to get the image file names for the current VO frame
						t = float(t_str) # timestamp 
						secs = int(t)
						nano_secs = int((t - float(secs)) * 1e9) 

						if vo_fn != "":
							pos = line_split[9:12] # [x,y,z]
							point = PointStamped()
							point.header.frame_id = frame_id
							point.header.stamp.secs = secs
							point.header.stamp.nsecs = nano_secs
							point.point.x = float(line_split[9])
							point.point.y = float(line_split[10])
							point.point.z = float(line_split[11])
							point_pub.publish(point)

						if im_dir != "":
							fl_nm = join(im_dir,"StereoImage__" + t_str)
							imL = imread(fl_nm + "-left.pnm")
							imR = imread(fl_nm + "-right.pnm")
							msgL = cvb.cv2_to_imgmsg(imL)
							msgL.header.frame_id = frame_id
							msgL.header.stamp.secs = secs
							msgL.header.stamp.nsecs = nano_secs
							msgR = cvb.cv2_to_imgmsg(imR)
							msgR.header.frame_id = frame_id
							msgR.header.stamp.secs = secs
							msgR.header.stamp.nsecs = nano_secs
							imL_pub.publish(msgL)
							imR_pub.publish(msgR)					
									
						rate.sleep()

if __name__ == '__main__':

	from argparse import ArgumentParser as Parser
	default_vo_fn = "NewCollege_3_11_2008__VO.dat"
	default_im_dir = "Stereo_Images"

	parser = Parser()
	parser.add_argument("-v", "--vo-file", dest="vo_fn", nargs='?', help="The file containing the VO data from the New College Dataset", default=default_vo_fn)
	parser.add_argument("-i", "--image-dir", dest="im_dir", nargs='?', help="The directory containing all the images from the New College Dataset.", default=default_im_dir)
	parser.add_argument("-r", "--rate", dest="rate", nargs='?', help="The rate at which to play back the data", default=1.0, type=float)
	args = parser.parse_args()	
	
	try:
		nc_publisher(args.vo_fn, args.im_dir, args.rate)
	except rospy.ROSInterruptException:
		pass
