Name: dpdk
Version: 1.7.0 
Release: 2%{?dist}
URL: http://dpdk.org
Source: http://dpdk.org/browse/dpdk/snapshot/dpdk-%{version}.tar.gz

Patch0: dpdk-debug.patch
Patch1: dpdk-config.patch


Summary: Data Plane Development Kit core

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

%global machine native

%global target x86_64-%{machine}-linuxapp-gcc



BuildRequires: kernel-devel, kernel-headers, libpcap-devel, doxygen

%description
DPDK core includes kernel modules, core libraries and tools.
testpmd application allows to test fast packet processing environments
on x86 platforms. For instance, it can be used to check that environment
can support fast path applications such as 6WINDGate, pktgen, rumptcpip, etc.
More libraries are available as extensions in other packages.


%package devel
Summary: Data Plane Development Kit core for development
Requires: %{name}%{?_isa} = %{version}-%{release}

%description devel
DPDK core-devel is a set of makefiles, headers, examples and documentation
for fast packet processing on x86 platforms.
More libraries are available as extensions in other packages.

%package doc
Summary: Data Plane Development Kit core programming API documentation
BuildArch: noarch

%description doc
DPDK core library API programming documentation

%global destdir %{buildroot}%{_prefix}
%global datadir %{_datadir}/%{name}-%{version}
%global docdir  %{_docdir}/%{name}-%{version}

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
cp -a  %{target}/include/*   %{buildroot}%{_includedir}/%{name}-%{version}
mkdir -p                     %{buildroot}%{_libdir}/%{name}-%{version}
cp -a  %{target}/lib/*       %{buildroot}%{_libdir}/%{name}-%{version}
mkdir -p                     %{buildroot}%{docdir}
cp -a  %{target}/doc/*       %{buildroot}%{docdir}
mkdir -p                     %{buildroot}%{datadir}
cp -a  %{target}/.config     %{buildroot}%{datadir}/config
cp -a  tools                 %{buildroot}%{datadir}

%files
# BSD
%dir %{datadir}
%{datadir}/config
# Theres no point in packaging any of the tools
# We currently don't need the igb uio script, there 
# are several uio scripts already available
# And the cpu_layout script functionality is 
# covered by lscpu
%exclude %{datadir}/tools
%{_bindir}/*
%{_libdir}/%{name}-%{version}

%files doc
#BSD
%{docdir}

%files devel
#BSD
%{_includedir}/*

%changelog
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

