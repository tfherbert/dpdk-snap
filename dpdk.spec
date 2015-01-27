Name: dpdk
Version: 1.7.0 
Release: 5%{?dist}
URL: http://dpdk.org
Source: http://dpdk.org/browse/dpdk/snapshot/dpdk-%{version}.tar.gz

Patch0: dpdk-debug.patch
Patch1: dpdk-config.patch


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



BuildRequires: kernel-headers, libpcap-devel, doxygen

%description
The Data Plane Development Kit is a set of libraries and drivers for
fast packet processing in the user space.

%package devel
Summary: Data Plane Development Kit development files
Requires: %{name}%{?_isa} = %{version}-%{release}

%description devel
This package contains the headers and other files needed for developing
applications with the Data Plane Development Kit.

%package doc
Summary: Data Plane Development Kit API documentation
BuildArch: noarch

%description doc
API programming documentation for the Data Plane Development Kit.

%define datadir %{_datadir}/%{name}-%{version}
%define docdir  %{_docdir}/%{name}-%{version}

%prep
%setup -q
%patch0 -p1 -z .debug
%patch1 -p1 -z .config

%build
export EXTRA_CFLAGS="%{optflags}"

# DPDK defaults to using builder-specific compiler flags.  However,
# the config has been changed by specifying CONFIG_RTE_MACHINE=default
# in order to build for a more generic host.  NOTE: It is possible that
# the compiler flags used still won't work for all Fedora-supported
# machines, but runtime checks in DPDK will catch those situations.

make V=1 O=%{target} T=%{target} %{?_smp_mflags} config
make V=1 O=%{target} %{?_smp_mflags}
make V=1 O=%{target} %{?_smp_mflags} doc

%install

# DPDK's "make install" seems a bit broken -- do things manually...

mkdir -p                     %{buildroot}%{_bindir}
cp -a  %{target}/app/testpmd %{buildroot}%{_bindir}/testpmd-%{version}
mkdir -p                     %{buildroot}%{_includedir}/%{name}-%{version}
cp -Lr  %{target}/include/*   %{buildroot}%{_includedir}/%{name}-%{version}
mkdir -p                     %{buildroot}%{_libdir}/%{name}-%{version}
cp -a  %{target}/lib/*       %{buildroot}%{_libdir}/%{name}-%{version}
mkdir -p                     %{buildroot}%{docdir}
cp -a  %{target}/doc/*       %{buildroot}%{docdir}
mkdir -p                     %{buildroot}%{datadir}
cp -a  %{target}/.config     %{buildroot}%{datadir}/config
# Theres no point in packaging any of the tools
# We currently don't need the igb uio script, there
# are several uio scripts already available
# And the cpu_layout script functionality is
# covered by lscpu
#cp -a  tools                 %{buildroot}%{datadir}

# Fixup irregular modes in headers
find %{buildroot}%{_includedir}/%{name}-%{version} -type f | xargs chmod 0644

%files
# BSD
%dir %{datadir}
%{datadir}/config
%{_bindir}/*
%{_libdir}/%{name}-%{version}

%files doc
#BSD
%{docdir}

%files devel
#BSD
%{_includedir}/*

%changelog
* Tue Jan 27 2015 Panu Matilainen <pmatilai@redhat.com> - 1.7.0-5
- Avoid unnecessary use of %%global, lazy expansion is normally better
- Drop unused destdir macro while at it

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

