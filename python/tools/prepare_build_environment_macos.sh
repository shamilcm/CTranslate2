#! /bin/bash

set -e
set -x

# Install OneAPI MKL
# See https://github.com/oneapi-src/oneapi-ci for installer URLs
ONEAPI_INSTALLER_URL=https://registrationcenter-download.intel.com/akdlm/irc_nas/18342/m_BaseKit_p_2022.1.0.92_offline.dmg
wget -q $ONEAPI_INSTALLER_URL
hdiutil attach -noverify -noautofsck $(basename $ONEAPI_INSTALLER_URL)
sudo /Volumes/$(basename $ONEAPI_INSTALLER_URL .dmg)/bootstrapper.app/Contents/MacOS/bootstrapper --silent --eula accept --components intel.oneapi.mac.mkl.devel

# Install LLVM's libomp because Intel's OpenMP runtime included in MKL does
# not ship with the header file.
brew install libomp

pip install "cmake==3.18.4"

mkdir build-release && cd build-release
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_CLI=OFF -DCMAKE_INSTALL_RPATH_USE_LINK_PATH=ON -DCMAKE_CXX_FLAGS="-Wno-unused-command-line-argument" ..
make -j$(sysctl -n hw.physicalcpu_max) install
cd ..
rm -r build-release

cp README.md python/
