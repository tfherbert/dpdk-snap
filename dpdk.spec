# Add option to disable combined library (--without combined)
%bcond_without combined
# Add option to build as static libraries (--without shared)
%bcond_without shared
# Add option to build without examples
%bcond_without examples

# Dont edit Version: and Release: directly, only these:
%define ver 2.0.0
%define rel 1
%define snapver 1695.gitc2ce3924

%define srcver %{ver}%{?snapver:-%{snapver}}

Name: dpdk
Version: %{ver}
Release: %{?snapver:0.%{snapver}.}%{rel}%{?dist}
URL: http://dpdk.org
Source: http://dpdk.org/browse/dpdk/snapshot/dpdk-%{srcver}.tar.gz

# Only needed for creating snapshot tarballs, not used in build itself
Source100: dpdk-snapshot.sh

Patch1: dpdk-config.patch
Patch2: dpdk-i40e-wformat.patch
Patch3: dpdk-1.8-libext.patch
Patch4: dpdk-dtneeded.patch
Patch5: dpdk-vhost-make.patch

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
# currently (and likely never will) run on non-x86 platforms
#
ExclusiveArch: x86_64 

%define machine native

%define target x86_64-%{machine}-linuxapp-gcc



BuildRequires: kernel-headers, libpcap-devel, fuse-devel
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
%setup -q -n %{name}-%{version}%{?snapver:-%{snapver}}
%patch1 -p1 -z .config
%patch2 -p1 -z .i40e-wformat
%if 0%{!?snapver}
%patch3 -p1 -b .libext
%endif
%patch4 -p1 -z .dtneeded
%if 0%{!?snapver}
%patch5 -p1 -z .vhost-make
%endif

%if %{with shared}
sed -i 's:^CONFIG_RTE_BUILD_SHARED_LIB=n$:CONFIG_RTE_BUILD_SHARED_LIB=y:g' config/common_linuxapp
%endif


%build
# Avoid appending second -Wall to everything, it breaks hand-picked
# disablers like per-file -Wno-strict-aliasing
export EXTRA_CFLAGS="-Wno-error `echo %{optflags} | sed -e 's:-Wall::g'` -fPIC"

# DPDK defaults to using builder-specific compiler flags.  However,
# the config has been changed by specifying CONFIG_RTE_MACHINE=default
# in order to build for a more generic host.  NOTE: It is possible that
# the compiler flags used still won't work for all Fedora-supported
# machines, but runtime checks in DPDK will catch those situations.

make V=1 O=%{target} T=%{target} %{?_smp_mflags} config
make V=1 O=%{target} %{?_smp_mflags}
make V=1 O=%{target} %{?_smp_mflags} doc

%if %{with examples}
make V=1 O=%{target}/examples T=%{target} %{?_smp_mflags} examples
%endif

%install

# DPDK's "make install" seems a bit broken -- do things manually...

mkdir -p                     %{buildroot}%{_bindir}
cp -a  %{target}/app/testpmd %{buildroot}%{_bindir}/testpmd-%{version}
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

# Theres no point in packaging any of the tools
# We currently don't need the igb uio script, there
# are several uio scripts already available
# And the cpu_layout script functionality is
# covered by lscpu
#cp -a  tools                 %{buildroot}%{datadir}

# Fixup irregular modes in headers
find %{buildroot}%{_includedir}/%{name}-%{version} -type f | xargs chmod 0644

# Upstream has an option to build a combined library but it'll clash
# with symbol/library versioning once it lands. Use a linker script to
# avoid the issue. Linking against the script during build resolves
# into links to the actual used libraries which is just fine for us,
# so this combined library is a build-time only construct now.
%if %{with combined}
comblib=libintel_dpdk.${libext}

echo "GROUP (" > ${comblib}
find %{buildroot}/%{_libdir}/ -name "*.${libext}" |\
	sed -e "s:^%{buildroot}/:  :g" >> ${comblib}
echo ")" >> ${comblib}
install -m 644 ${comblib} %{buildroot}/%{_libdir}/${comblib}
%endif

%if %{with shared}
%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig
%endif

%files
# BSD
%{_bindir}/testpmd*
%if %{with shared}
%{_libdir}/*.so.*
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
%else
%{_libdir}/*.a
%endif

%if %{with examples}
%files examples
%{_bindir}/dpdk_*
%endif

%changelog
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

