# Copyright 2025 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path
from mash.SPDXLicense import is_spdx_license, map_license
from mash.rosdep_support import resolve_rosdep_key

ROS_DISTRO_DEFAULT = "rolling"

class BitbakeRecipe:
    recipe_boilerplate = "\
# Recipe created by mash\n\
#\n\
# Copyright (c) 2025 Open Source Robotics Foundation, Inc.\n\
"
    recipe_depends = "\
DEPENDS = \"${ROS_BUILD_DEPENDS} ${ROS_BUILDTOOL_DEPENDS}\"\n\
# Bitbake doesn\'t support the \"export\" concept, so build them as if we needed\n\
# them to build this package (even though we actually don\'t) so that they\'re\n\
# guaranteed to have been staged should this package appear in another\'s\n\
# DEPENDS.\n\
DEPENDS += \"${ROS_EXPORT_DEPENDS} ${ROS_BUILDTOOL_EXPORT_DEPENDS}\"\n\
\n\
RDEPENDS:${PN} += \"${ROS_EXEC_DEPENDS}\"\n\
"
    ROS_PLATFORM_NAME = "openembedded"

    def __init__(self):
        self.name = None
        self.version = None
        self.summary = None
        self.description = None
        self.homepage = None
        self.author = None
        self.maintainer = None

        self.rosdistro = ROS_DISTRO_DEFAULT

        self.internal_packages = []

        self.section = None

        # license should be an SPDX identifier
        self.license = []

        self.lic_files_chksum = None

        self.src_uri = None
        self.srcrev = None
        self.branch = None

        self.pkg_path = None

        self.build_type = None

    def set_rosdistro(self, rosdistro):
        self.rosdistro = rosdistro

    # Set a list of internal packages (released in the same distro)
    def set_internal_packages(self, internal_packages):
        # print(f"DEBUG: Print internal packages:\n{internal_packages}")

        self.internal_packages = internal_packages

    def importPackage(self, pkg):
        self.name = pkg.name
        self.version = pkg.version

        self.summary = None
        self.description = pkg.description
        self.homepage = pkg.homepage

        if pkg.author_name and pkg.author_email:
            self.author = f"{pkg.author_name} <{pkg.author_email}>"
        elif pkg.author_name:
            self.author = pkg.author_name
        else:
            self.author = None

        if pkg.upstream_name and pkg.upstream_email:
            self.maintainer = f"{pkg.upstream_name} <{pkg.upstream_email}>"
        elif pkg.upstream_name:
            self.maintainer = pkg.upstream_email
        else:
            self.maintainer = None

        # license should be an SPDX identifier
        self.license = []
        for license_str in pkg.upstream_license:
            if (is_spdx_license(license_str)):
                self.license.append(license_str)
            else:
                spdx_license = map_license(license_str)
                if (len(spdx_license) > 0):
                    # print("mapped {} to {}".format(license_str, spdx_license))
                    self.license.append(spdx_license)
                else:
                    self.license.append(license_str)

        self.license_line = pkg.license_line
        self.license_md5 = pkg.license_md5

        self.build_depends = [self.convert_to_oe_naming(obj) for obj in pkg.build_depends]
        self.build_export_depends = [self.convert_to_oe_naming(obj) for obj in pkg.build_export_depends]
        self.buildtool_depends = [self.convert_to_oe_naming(obj, True) for obj in pkg.buildtool_depends]
        self.buildtool_export_depends = [self.convert_to_oe_naming(obj, True) for obj in pkg.buildtool_export_depends]
        self.exec_depends = [self.convert_to_oe_naming(obj) for obj in pkg.exec_depends]
        self.run_depends = [self.convert_to_oe_naming(obj) for obj in pkg.run_depends]
        self.test_depends = [self.convert_to_oe_naming(obj) for obj in pkg.test_depends]
        self.doc_depends = [self.convert_to_oe_naming(obj) for obj in pkg.doc_depends]

        self.build_type = pkg.build_type

    def convert_to_oe_naming(self, ros_pkgname, isNative=False):
        oe_pkgname = ""
        result = ""

        if str(ros_pkgname) in self.internal_packages:
           oe_pkgname = str(ros_pkgname)
           oe_pkgname = oe_pkgname.lower().replace('_', '-')
        else:
            # print(f"Resolving external package: {ros_pkgname}, {self.ROS_PLATFORM_NAME}, {self.rosdistro}")
            try:
                (resolved_key, _, _) = \
                    resolve_rosdep_key(str(ros_pkgname), self.ROS_PLATFORM_NAME, '', self.rosdistro)

                result = resolved_key[0]
            except Exception as e:
                result = None
                print(f"\t- Warning: Could not resolve external package {ros_pkgname}: {e}")

                pass

            if result:
                # Remove any layer information from the first resolved key
                # print(f"DEBUG: Resolved rosdep key {ros_pkgname} to {result} {type(result)}")
                oe_pkgname = str(result).split('@')[0]

                # OpenEmbedded entries should already follow OE naming convention
                # oe_pkgname = oe_pkgname.lower().replace('_', '-')
            else:
                # Fallback to ROS package name conversion
                oe_pkgname = str(ros_pkgname)
                oe_pkgname = oe_pkgname.lower().replace('_', '-')
                print(f"\t- Falling back to using OE-naming convention: {oe_pkgname}")

        if isNative:
            oe_pkgname = oe_pkgname + "-native"

        return oe_pkgname

    def bitbake_recipe_filename(self):
        recipename = self.name.replace('_', '-')
        return f"{recipename}_{self.version}.bb"

    @staticmethod
    def get_multiline_variable(name, value):
        indent = ' ' * 4
        lines = []
        if len(value) == 0:
            lines.append(f'{name} = ""')
        else:
            lines.append(f'{name} = "\\')
            if isinstance(value, str):
                    for line in value.splitlines():
                        lines.append(f'{indent}{line.strip()}\\')
            elif isinstance(value, list):
                for item in value:
                    lines.append(f'{indent}{item}\\')
            else:
                raise TypeError("value must be str or list, found {}".format(type(value)))
            lines.append('"')

        return "\n".join(lines)

    def set_git_metadata(self, src_uri, branch, srcrev, repo_name, tag_name):
        self.src_uri = src_uri
        self.srcrev = srcrev
        self.branch = branch
        self.repo_name = repo_name
        self.tag_name = tag_name
        # print(f"Set git metadata: SRC_URI={self.src_uri}, BRANCH={self.branch}, SRCREV={self.srcrev}, TAG={self.tag_name}")

    def set_pkg_path(self, pkg_path):
        self.pkg_path = pkg_path

    def get_recipe_text(self):
        lines = []
        lines.append(self.recipe_boilerplate)
        lines.append(f"inherit ros_distro_{self.rosdistro}")
        lines.append(f"inherit mash_generated")
        lines.append("")

        if self.summary:
            lines.append(f'SUMMARY = "{self.summary}"')

        if '\n' in self.description:
            lines.append(self.get_multiline_variable('DESCRIPTION', self.description))
        else:
            lines.append(f'DESCRIPTION = "{self.description}"')

        lines.append(f'AUTHOR = "{self.maintainer}"')
        if self.author:
            lines.append(f'ROS_AUTHOR = "{self.author}"')

        lines.append(f'HOMEPAGE = "{self.homepage}"')
        if self.section:
            lines.append(f'SECTION = "{self.section}"')
        license_expression = " & ".join(self.license)
        lines.append(f'LICENSE = "{license_expression}"')

        lines.append(f'LIC_FILES_CHKSUM = "file://package.xml;beginline={self.license_line};endline={self.license_line};md5={self.license_md5}"')

        lines.append("")
        lines.append(f'ROS_CN = "{self.repo_name}"')
        lines.append(f'ROS_BPN = "{self.name}"')
        lines.append("")

        lines.append(self.get_multiline_variable('ROS_BUILD_DEPENDS', self.build_depends))
        lines.append("")
        lines.append(self.get_multiline_variable('ROS_BUILDTOOL_DEPENDS', self.buildtool_depends))
        lines.append("")
        lines.append(self.get_multiline_variable('ROS_EXPORT_DEPENDS', self.build_export_depends))
        lines.append("")
        lines.append(self.get_multiline_variable('ROS_BUILDTOOL_EXPORT_DEPENDS', self.buildtool_export_depends))
        lines.append("")
        lines.append(self.get_multiline_variable('ROS_EXEC_DEPENDS', self.exec_depends))
        lines.append("")
        lines.append("# Currently informational only -- see http://www.ros.org/reps/rep-0149.html#dependency-tags.")
        lines.append(self.get_multiline_variable('ROS_TEST_DEPENDS', self.test_depends))
        lines.append("")
        # if self.run_depends:
        #     lines.append(self.get_multiline_variable('ROS_RUN_DEPENDS', self.run_depends))
        # if self.doc_depends:
        #     lines.append(self.get_multiline_variable('ROS_DOC_DEPENDS', self.doc_depends))

        lines.append(self.recipe_depends)

        lines.append(f'ROS_BRANCH ?= "branch={self.branch}"')
        lines.append(f'SRC_URI = "{self.src_uri}"')
        lines.append(f'SRCREV = "{self.srcrev}"')

        # XXX: Only use WORKDIR for older Yocto releases like scarthgap
        lines.append(f'S = "${{WORKDIR}}/git{self.pkg_path}"')

        lines.append("")
        lines.append(f"ROS_BUILD_TYPE = \"{self.build_type}\"")
        lines.append("")
        lines.append("inherit ros_${ROS_BUILD_TYPE}")

        return "\n".join(lines) + "\n"
