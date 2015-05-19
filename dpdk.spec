# Add option to build as static libraries (--without shared)
%bcond_without shared
# Add option to build without examples
%bcond_without examples
# Add option to build without tools
%bcond_without tools
# Add option to build with IVSHMEM support (clashes with other stuff?)
%bcond_with ivshmem

# Copr exhibits strange problems with parallel build. It also overrides
# _smp_mflags with a version that doesn't grok _smp_ncpus_max. Grumble.
%define _smp_mflags %{nil}

# Dont edit Version: and Release: directly, only these:
%define ver 2.0.0
%define rel 7
# Define when building git snapshots
#define snapver 2086.git263333bb

%define srcver %{ver}%{?snapver:-%{snapver}}

Name: dpdk
Version: %{ver}
Release: %{?snapver:0.%{snapver}.}%{rel}%{?dist}
URL: http://dpdk.org
Source: http://dpdk.org/browse/dpdk/snapshot/dpdk-%{srcver}.tar.gz

# Only needed for creating snapshot tarballs, not used in build itself
Source100: dpdk-snapshot.sh

Patch1: dpdk-2.0-eventlink.patch
Patch2: dpdk-i40e-wformat.patch
Patch4: dpdk-dtneeded.patch
Patch5: dpdk-dev-vhost-flush-used--idx-update-before-reading-avail--flags.patch
Patch6: dpdk-dev-vfio-eventfd-should-be-non-block-and-not-inherited.patch

Summary: Set of libraries and drivers for fast packet processing

#
# Note that, while this is dual licensed, all code that is included with this
# Pakcage are BSD licensed. The only files that aren't licensed via BSD is the
# kni kernel module which is dual LGPLv2/BSD, and thats not built for fedora.
#
License: BSD and LGPLv2 and GPLv2

#
# The DPDK is designed to optimize througput of network traffic using, among
# other techniques, carefully crafted x86 assembly instructions.  As such it
# currently (and likely never will) run on non-x86 platforms. 
ExclusiveArch: x86_64 

%define machine native

%define target x86_64-%{machine}-linuxapp-gcc

BuildRequires: kernel-headers, libpcap-devel
BuildRequires: doxygen, python-sphinx

%description
The Data Plane Development Kit is a set of libraries and drivers for
fast packet processing in the user space.

%package devel
Summary: Data Plane Development Kit development files
Requires: %{name}%{?_isa} = %{version}-%{release}
%if ! %{with shared}
Provides: %{name}-static = %{version}-%{release}
%endif

%description devel
This package contains the headers and other files needed for developing
applications with the Data Plane Development Kit.

%package doc
Summary: Data Plane Development Kit API documentation
BuildArch: noarch

%description doc
API programming documentation for the Data Plane Development Kit.

%if %{with tools}
%package tools
Summary: Tools for setting up Data Plane Development Kit environment
Requires: %{name} = %{version}-%{release}
Requires: kmod pciutils findutils iproute

%description tools
%{summary}
%endif

%if %{with examples}
%package examples
Summary: Data Plane Development Kit example applications
BuildRequires: libvirt-devel

%description examples
Example applications utilizing the Data Plane Development Kit, such
as L2 and L3 forwarding.
%endif

%define sdkdir  %{_libdir}/%{name}-%{version}-sdk
%define docdir  %{_docdir}/%{name}-%{version}

%prep
%setup -q -n %{name}-%{srcver}
%patch1 -p1 -z .eventlink-alias
%patch2 -p1 -z .i40e-wformat
%patch4 -p1 -z .dtneeded
%patch5 -p1 -z .vhost-flush
%patch6 -p1 -z .vfio-eventfd

%build
function setconf()
{
    cf=%{target}/.config
    if grep -q $1 $cf; then
        sed -i "s:^$1=.*$:$1=$2:g" $cf
    else
        echo $1=$2 >> $cf
    fi
}
# In case dpdk-devel is installed
unset RTE_SDK RTE_INCLUDE RTE_TARGET

# Avoid appending second -Wall to everything, it breaks hand-picked
# disablers like per-file -Wno-strict-aliasing
export EXTRA_CFLAGS="`echo %{optflags} | sed -e 's:-Wall::g'` -fPIC -Wno-error=array-bounds"


make V=1 O=%{target} T=%{target} %{?_smp_mflags} config

# DPDK defaults to optimizing for the builder host we need generic binaries
setconf CONFIG_RTE_MACHINE default

# Enable pcap and vhost build, the added deps are ok for us
setconf CONFIG_RTE_LIBRTE_PMD_PCAP y
setconf CONFIG_RTE_LIBRTE_VHOST y

# If IVSHMEM enabled...
%if %{with ivshmem}
    setconf CONFIG_RTE_LIBRTE_IVSHMEM y
    setconf CONFIG_RTE_LIBRTE_IVSHMEM_DEBUG n
    setconf CONFIG_RTE_LIBRTE_IVSHMEM_MAX_PCI_DEVS 4
    setconf CONFIG_RTE_LIBRTE_IVSHMEM_MAX_ENTRIES 128
    setconf CONFIG_RTE_LIBRTE_IVSHMEM_MAX_METADATA_FILES 32
    setconf CONFIG_RTE_EAL_SINGLE_FILE_SEGMENTS y
%endif

%if %{with shared}
setconf CONFIG_RTE_BUILD_SHARED_LIB y
%endif

# Disable kernel modules
setconf CONFIG_RTE_EAL_IGB_UIO n
setconf CONFIG_RTE_LIBRTE_KNI n

make V=1 O=%{target} %{?_smp_mflags} 

# Creating PDF's has excessive build-requirements, html docs suffice fine
make V=1 O=%{target} %{?_smp_mflags} doc-api-html doc-guides-html

%if %{with examples}
make V=1 O=%{target}/examples T=%{target} %{?_smp_mflags} examples
%endif

%install

# DPDK's "make install" seems a bit broken -- do things manually...

mkdir -p                     %{buildroot}%{_bindir}
cp -a  %{target}/app/testpmd %{buildroot}%{_bindir}/testpmd
mkdir -p                     %{buildroot}%{_includedir}/%{name}-%{version}
cp -Lr  %{target}/include/*   %{buildroot}%{_includedir}/%{name}-%{version}
mkdir -p                     %{buildroot}%{_libdir}
cp -a  %{target}/lib/*       %{buildroot}%{_libdir}
mkdir -p                     %{buildroot}%{docdir}
cp -a  %{target}/doc/*       %{buildroot}%{docdir}

%if %{with shared}
libext=so
%else
libext=a
%endif

# DPDK apps expect a particular (and somewhat peculiar) directory layout
# for building, arrange for that
mkdir -p                     %{buildroot}%{sdkdir}/lib
mkdir -p                     %{buildroot}%{sdkdir}/%{target}
cp -a  %{target}/.config     %{buildroot}%{sdkdir}/%{target}
ln -s  ../../../include/%{name}-%{version} %{buildroot}%{sdkdir}/%{target}/include
cp -a  mk/                   %{buildroot}%{sdkdir}
mkdir -p                     %{buildroot}%{sdkdir}/scripts
cp -a  scripts/*.sh          %{buildroot}%{sdkdir}/scripts

%if %{with tools}
cp -p  tools/*.py            %{buildroot}%{_bindir}
%endif

%if %{with examples}
find %{target}/examples/ -name "*.map" | xargs rm -f
for f in %{target}/examples/*/%{target}/app/*; do
    bn=`basename ${f}`
    cp -p ${f} %{buildroot}%{_bindir}/dpdk_${bn}
done
%endif

# Create library symlinks for the "sdk"
for f in %{buildroot}/%{_libdir}/*.${libext}; do
    l=`basename ${f}`
    ln -s ../../${l} %{buildroot}/%{sdkdir}/lib/${l}
done

# Setup RTE_SDK environment as expected by apps etc
mkdir -p %{buildroot}/%{_sysconfdir}/profile.d
cat << EOF > %{buildroot}/%{_sysconfdir}/profile.d/dpdk-sdk-%{_arch}.sh
if [ -z "\${RTE_SDK}" ]; then
    export RTE_SDK="%{sdkdir}"
    export RTE_TARGET="%{target}"
    export RTE_INCLUDE="%{_includedir}/%{name}-%{version}"
fi
EOF

cat << EOF > %{buildroot}/%{_sysconfdir}/profile.d/dpdk-sdk-%{_arch}.csh
if ( ! \$RTE_SDK ) then
    setenv RTE_SDK "%{sdkdir}"
    setenv RTE_TARGET "%{target}"
    setenv RTE_INCLUDE "%{_includedir}/%{name}-%{version}"
endif
EOF

# Fixup irregular modes in headers
find %{buildroot}%{_includedir}/%{name}-%{version} -type f | xargs chmod 0644

# Upstream has an option to build a combined library but it's bloatware which
# wont work at all when library versions start moving, replace it with a 
# linker script which avoids these issues. Linking against the script during
# build resolves into links to the actual used libraries which is just fine
# for us, so this combined library is a build-time only construct now.
comblib=libintel_dpdk.${libext}

echo "GROUP (" > ${comblib}
find %{buildroot}/%{_libdir}/ -maxdepth 1 -name "*.${libext}" |\
	sed -e "s:^%{buildroot}/:  :g" >> ${comblib}
echo ")" >> ${comblib}
install -m 644 ${comblib} %{buildroot}/%{_libdir}/${comblib}

%files
# BSD
%{_bindir}/testpmd
%if %{with shared}
%{_libdir}/*.so.*
%{_libdir}/*_pmd_*.so
%endif

%files doc
#BSD
%{docdir}

%files devel
#BSD
%{_includedir}/*
%{sdkdir}
%{_sysconfdir}/profile.d/dpdk-sdk-*.*
%if %{with shared}
%{_libdir}/*.so
%exclude %{_libdir}/*_pmd_*.so
%else
%{_libdir}/*.a
%endif

%if %{with examples}
%files examples
%{_bindir}/dpdk_*
%exclude %{_bindir}/*.py
%endif

%if %{with tools}
%files tools
%{_bindir}/*.py
%endif

%changelog
* Tue May 19 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-7
- Drop pointless build conditional, the linker script is here to stay
- Drop vhost-cuse build conditional, vhost-user is here to stay
- Cleanup comments a bit

* Thu Apr 30 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-6
- Fix potential hang and thread issues with VFIO eventfd

* Fri Apr 24 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-5
- Fix a potential hang due to missed interrupt in vhost library

* Tue Apr 21 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-4
- Drop unused pre-2.0 era patches
- Handle vhost-user/cuse selection automatically based on the copr repo name

* Fri Apr 17 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-3
- Dont depend on fuse when built for vhost-user support
- Drop version from testpmd binary, we wont be parallel-installing that

* Thu Apr 09 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-2
- Remove the broken kmod stuff
- Add a new dkms-based eventfd_link subpackage if vhost-cuse is enabled

* Tue Apr 07 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-1
- Update to 2.0 final (http://dpdk.org/doc/guides-2.0/rel_notes/index.html)

* Thu Apr 02 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2086.git263333bb.2
- Switch (back) to vhost-user, thus disabling vhost-cuse support
- Build requires fuse-devel for now even when fuse is unused

* Thu Apr 02 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2086.git263333bb.1
- New snapshot

* Tue Mar 31 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2081.gitf14db469.1
- New snapshot

* Mon Mar 30 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2049.git2f95a470.1
- New snapshot
- Add spec option for enabling vhost-user instead of vhost-cuse
- Build requires fuse-devel only with vhost-cuse
- Add virtual provide for vhost user/cuse tracking 

* Fri Mar 27 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2038.git91a8743e.3
- Disable vhost-user for now to get vhost-cuse support, argh.

* Fri Mar 27 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2038.git91a8743e.2
- Add a bunch of missing dependencies to -tools

* Thu Mar 26 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2038.git91a8743e.1
- Another day, another snapshot
- Disable IVSHMEM support for now, it seems to break other stuff

* Mon Mar 23 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2034.gitb79a038d.1
- Another day, another snapshot

* Fri Mar 20 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2022.gitfe4810a0.2
- Dont fail build for array bounds warnings for now, gcc 5 is emitting a bunch

* Fri Mar 20 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2022.gitfe4810a0.1
- Another day, another snapshot
- Avoid building pdf docs

* Wed Mar 18 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.2014.git1a5994ac.1
- Another day, another snapshot

* Tue Mar 10 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1959.git4d2c67be.1
- Another day, another snapshot

* Mon Mar 09 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1955.gitf2552cd5.1
- Another day, another snapshot

* Thu Mar 05 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1933.gitf2cae314.1
- Another day, another snapshot

* Wed Mar 04 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1916.gita001589e.3
- Fix yet another missing symbol export

* Tue Mar 03 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1916.gita001589e.2
- Add missing dependency to tools -subpackage

* Tue Mar 03 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1916.gita001589e.1
- New snapshot
- Work around #1198009

* Mon Mar 02 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1911.gitffc468ff.2
- Optionally package tools too, some binding script is needed for many setups

* Mon Mar 02 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1911.gitffc468ff.1
- New snapshot
- Disable kernel module build by default
- Add patch to fix missing defines/includes for external applications

* Fri Feb 27 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1906.git00c68563.1
- New snapshot
- Remove bogus devname module alias from eventfd-link module
- Whack evenfd-link to honor RTE_KERNELDIR too

* Thu Feb 26 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1903.gitb67578cc.3
- Add spec option to build kernel modules too
- Build eventfd-link module too if kernel modules enabled

* Thu Feb 26 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1903.gitb67578cc.2
- Move config changes from spec after "make config" to simplify things
- Move config changes from dpdk-config patch to the spec

* Thu Feb 26 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1903.gitb67578cc.1
- New day, new snapshot...

* Wed Feb 25 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1872.git1c29883c.1
- New snapshot
- Disable broken jobstats example, fix missing symbols

* Tue Feb 24 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1842.git6052e07a.1
- New snapshot
- Upstreamable ixgbe build fix

* Tue Feb 24 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1838.gite14b969a.1
- New snapshot, including eg vhost-user support

* Mon Feb 23 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1790.git7a18146d.1
- New snapshot, including eg unified virtio support

* Fri Feb 20 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1726.git3c210048.1
- New snapshot

* Fri Feb 20 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1720.gita8c50a37.1
- New snapshot
- Drop no longer needed symver patch

* Thu Feb 19 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1717.gitd3aa5274.2
- Fix warnings tripping up build with gcc 5, remove -Wno-error

* Thu Feb 19 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1717.gitd3aa5274.1
- New snapshot

* Wed Feb 18 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1698.gitc07691ae.1
- Move the unversioned .so links for plugins into main package
- New snapshot

* Wed Feb 18 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1695.gitc2ce3924.3
- Fix missing symbol export for rte_eal_iopl_init()
- Only mention libs once in the linker script

* Wed Feb 18 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1695.gitc2ce3924.2
- Fix gcc version logic to work with 5.0 too

* Wed Feb 18 2015 Panu Matilainen <pmatilai@redhat.com> - 2.0.0-0.1695.gitc2ce3924.1
- Add spec magic to easily switch between stable and snapshot versions
- Add tarball snapshot script for reference
- Update to pre-2.0 git snapshot

* Thu Feb 12 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-15
- Disable -Werror, this is not useful behavior for released versions

* Wed Feb 11 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-14
- Fix typo causing librte_vhost missing DT_NEEDED on fuse

* Wed Feb 11 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-13
- Fix vhost library linkage
- Add spec option to build example applications, enable by default

* Fri Feb 06 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-12
- Enable librte_acl build
- Enable librte_ivshmem build

* Thu Feb 05 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-11
- Drop the private libdir, not needed with versioned libs

* Thu Feb 05 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-10
- Drop symbol versioning patches, always do library version for shared
- Add comment on the combined library thing

* Wed Feb 04 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-9
- Add missing symbol version to librte_cmdline

* Tue Feb 03 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-8
- Set soname of the shared libraries
- Fixup typo in ld path config file name

* Tue Feb 03 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-7
- Add library versioning patches as another build option, enable by default

* Tue Feb 03 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-6
- Add our libraries to ld path & run ldconfig when using shared libs

* Fri Jan 30 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-5
- Add DT_NEEDED for external dependencies (pcap, fuse, dl, pthread)
- Enable combined library creation, needed for OVS
- Enable shared library creation, needed for sanity

* Thu Jan 29 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-4
- Include scripts directory in the "sdk" too

* Thu Jan 29 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-3
- Fix -Wformat clash preventing i40e driver build, enable it
- Fix -Wall clash preventing enic driver build, enable it

* Thu Jan 29 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-2
- Enable librte_vhost, which buildrequires fuse-devel
- Enable physical NIC drivers that build (e1000, ixgbe) for VFIO use

* Thu Jan 29 2015 Panu Matilainen <pmatilai@redhat.com> - 1.8.0-1
- Update to 1.8.0

* Wed Jan 28 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-8
- Always build with -fPIC

* Wed Jan 28 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-7
- Policy compliance: move static libraries to -devel, provide dpdk-static
- Add a spec option to build as shared libraries

* Wed Jan 28 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-6
- Avoid variable expansion in the spec here-documents during build
- Drop now unnecessary debug flags patch
- Add a spec option to build a combined library

* Tue Jan 27 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-5
- Avoid unnecessary use of %%global, lazy expansion is normally better
- Drop unused destdir macro while at it
- Arrange for RTE_SDK environment + directory layout expected by DPDK apps
- Drop config from main package, it shouldn't be needed at runtime

* Tue Jan 27 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-4
- Copy the headers instead of broken symlinks into -devel package
- Force sane mode on the headers
- Avoid unnecessary %%exclude by not copying unpackaged content to buildroot
- Clean up summaries and descriptions
- Drop unnecessary kernel-devel BR, we are not building kernel modules

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jul 17 2014 - John W. Linville <linville@redhat.com> - 1.7.0-2
- Use EXTRA_CFLAGS to include standard Fedora compiler flags in build
- Set CONFIG_RTE_MACHINE=default to build for least-common-denominator machines
- Turn-off build of librte_acl, since it does not build on default machines
- Turn-off build of physical device PMDs that require kernel support
- Clean-up the install rules to match current packaging
- Correct changelog versions 1.0.7 -> 1.7.0
- Remove ix86 from ExclusiveArch -- it does not build with above changes

* Thu Jul 10 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-1.0
- Update source to official 1.7.0 release 

* Thu Jul 03 2014 - Neil Horman <nhorman@tuxdriver.com>
- Fixing up release numbering

* Tue Jul 01 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.9.1.20140603git5ebbb1728
- Fixed some build errors (empty debuginfo, bad 32 bit build)

* Wed Jun 11 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.9.20140603git5ebbb1728
- Fix another build dependency

* Mon Jun 09 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.8.20140603git5ebbb1728
- Fixed doc arch versioning issue

* Mon Jun 09 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.7.20140603git5ebbb1728
- Added verbose output to build

* Tue May 13 2014 - Neil Horman <nhorman@tuxdriver.com> - 1.7.0-0.6.20140603git5ebbb1728
- Initial Build

