mash
====

Generate build recipes based on catkin package manifest (package.xml)  [format 2](https://www.ros.org/reps/rep-0140.html).

It is a standalone application that uses the colcon extensions to discover packages in a workspace.  It then reads the package manifest to get the metadata needed to create the [BitBake](https://docs.yoctoproject.org/bitbake/) recipe.

# Why mash?

The ROS tooling has a naming scheme based on willow trees and the OpenEmbedded tools use a cooking theme. The name matches both schemes and also makes a convenient action verb for a command-line tool.

"Poor people at one time often ate willow catkins that had been cooked to form a mash." <https://en.wikipedia.org/wiki/Willow>

# Installation

```
python -m venv myenv
source myenv/bin/activate
pip install --break-system-packages -r requirements.txt
pip install .
```

# Usage

After sourcing your venv, you may use mash to generate bitbake recipes for Space ROS.

Install vcs2l to retrieve Space ROS sources with vcs.
```
pip install vcs2l colcon-common-extensions

mkdir spaceros_ws
cd spaceros_ws
git clone https://github.com/space-ros/space-ros
mkdir src
vcs import src < ./space-ros/spaceros.repos
vcs import src < ./space-ros/ros2.repos
mash --ros-distro humble
```

# Contributing

Any contribution that you make to this repository will be under the [Apache 2.0 License](LICENSE-2.0.txt), unless explicitly stated otherwise.

Contributors must sign-off each commit by adding a `Signed-off-by: ...` line to commit messages to certify that they have the right to submit the code they are contributing to the project according to the [Developer Certificate of Origin (DCO)](https://developercertificate.org/).

# License

The source code for this project is under the Apache 2.0 license.  Text for the license can be found in the LICENSE-2.0.txt file in the project top level directory.  Dependencies may be under different licenses.
