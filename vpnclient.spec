%define name    vpnclient
%define version 4.8.02.0030
%define release 3

Name:           %{name}
Version:        %{version}
Release:        %{release}
Summary:        Cisco VPN client
License:        Commercial
Group:          Networking/Other
URL:            http://www.cisco.com/en/US/products/sw/secursw/ps2308/index.html
# http://projects.tuxx-home.at/?id=cisco_vpn_client
Source0:        http://tuxx-home.at/vpn/Linux/%{name}-linux-x86_64-%{version}-k9.tar.gz
Source1:        %{name}.bash-completion
Source2:	%{name}-wrapper
Source3:	%{name}.sysconfig
Patch0:         vpnclient-linux-2.6.19.diff
Patch1:         vpnclient-linux-2.6.22.diff
Patch2:		http://projects.tuxx-home.at/ciscovpn/patches/vpnclient-linux-2.6.24-final.diff
Patch3:		http://projects.tuxx-home.at/ciscovpn/patches/cisco_skbuff_offset.patch
Patch4:		vpnclient-linux-2.6.24-makefilefix.patch
Patch5:		vpnclient-interceptor.patch
Patch6:		vpnclient-4.8.02.0030-2.6.33.patch
Requires:       kmod(vpnclient)
ExclusiveArch:  %ix86
BuildRoot:      %{_tmppath}/%{name}-%{version}

%description
Simple to deploy and operate, the Cisco VPN Client allows organizations to
establish end-to-end, encrypted VPN tunnels for secure connectivity for mobile
employees or teleworkers. This thin design, IP security (IPSec)-implementation
is compatible with all Cisco virtual private network (VPN) products.

The Cisco VPN Client can be preconfigured for mass deployments, and initial
logins require little user intervention. It supports the innovative Cisco Easy
VPN capabilities, delivering a uniquely scalable, cost-effective, and
easy-to-manage remote access VPN architecture that eliminates the operational
costs associated with maintaining a consistent policy and key management
method. The Cisco Easy VPN feature allows the Cisco VPN Client to receive
security policies upon a VPN tunnel connection from the central site VPN device
(Cisco Easy VPN Server), minimizing configuration requirements at the remote
location. This simple and highly scalable solution is ideal for large remote
access deployments where it is impractical to individually configure policies
for multiple remote PCs.

%package -n	dkms-%{name}
Summary:	kernel module for %{name}
Group:		System/Kernel and hardware
Requires:	dkms
Requires(post):	dkms
Requires(preun): dkms
BuildArch:  noarch

%description -n dkms-%{name}
Kernel module for %{name}.

%prep
%setup -q -n %{name}
#patch0 -p 1
#patch1 -p 1
#%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p0
%patch6 -p1

%install
rm -rf %{buildroot}

install -d -m 755 %{buildroot}%{_bindir}
install -m 755 vpnclient cisco_cert_mgr ipseclog cvpnd %{buildroot}%{_bindir}
install -m 755 vpnclient %{buildroot}%{_bindir}/vpnclient.real
install -m 755 %{SOURCE2} %{buildroot}%{_bindir}/vpnclient
install -d -m755 %{buildroot}/%{_sysconfdir}/sysconfig/
install -m644 %{SOURCE3} %{buildroot}/%{_sysconfdir}/sysconfig/%{name}

install -d -m 755 %{buildroot}%{_libdir}
install -m 755 libvpnapi.so %{buildroot}%{_libdir}

install -d -m 755 %{buildroot}%{_includedir}
install -m 644 vpnapi.h %{buildroot}%{_includedir}

install -d -m 755 %{buildroot}%{_sysconfdir}/bash_completion.d
install -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/bash_completion.d/%{name}

install -d -m 755 %{buildroot}%{_sysconfdir}/opt/cisco-vpnclient
install -d -m 755 %{buildroot}%{_sysconfdir}/opt/cisco-vpnclient/Certificates
install -d -m 755 %{buildroot}%{_sysconfdir}/opt/cisco-vpnclient/Profiles
install -m 644 vpnclient.ini %{buildroot}%{_sysconfdir}/opt/cisco-vpnclient

install -d -m 755 %{buildroot}%{_var}/log/%{name}
pushd %{buildroot}%{_sysconfdir}/opt/cisco-vpnclient
ln -s ../../../var/log/%{name} Logs
popd

install -d -m 755 %{buildroot}/opt/cisco-vpnclient/bin
pushd %{buildroot}/opt/cisco-vpnclient/bin
ln -s ../../../usr/bin/cvpnd
popd

# dkms
install -d -m 755 %{buildroot}/usr/src/%{name}-%{version}-%{release}
install -m 644 *.c %{buildroot}/usr/src/%{name}-%{version}-%{release}
install -m 644 *.h %{buildroot}/usr/src/%{name}-%{version}-%{release}
install -m 644 Makefile %{buildroot}/usr/src/%{name}-%{version}-%{release}
install -m 755 libdriver64.so %{buildroot}/usr/src/%{name}-%{version}-%{release}
install -m 755 libdriver.so %{buildroot}/usr/src/%{name}-%{version}-%{release}
cat > %{buildroot}/usr/src/%{name}-%{version}-%{release}/dkms.conf <<'EOF'
PACKAGE_NAME="%{name}"
PACKAGE_VERSION="%{version}-%{release}"
DEST_MODULE_LOCATION="/kernel/net/ipv4"
BUILT_MODULE_NAME="cisco_ipsec"
MAKE="/bin/true && make KERNEL_SOURCES=$kernel_source_dir"
MODULES_CONF_ALIAS_TYPE="cipsec"
AUTOINSTALL="YES"
#BUILD_MAX_KERNEL=2.6.24
EOF

cat > README.urpmi <<EOF
mandriva RPM specific notes

setup
-----
The setup used here differs from default one, to achieve better FHS compliance.
- no init script needed, kernel module is loaded on demand
- the binaries are in %{_bindir}, and only a symlink is provided under /opt, 
  as the client hardcode cvpnd location

wrapper script
--------------
Due to Cisco not supporting SMP kernels, and the resulting kernel hangs that
occur for many under SMP kernels (often when using vpnclient over a wifi
connection), a wrapper script has been included which will disable all but
the first CPU (or core) when starting vpnclient, and enable them again when
vpnclient exits. The behaviour of the script can be modified by editing
%{_sysconfdir}/sysconfig/vpnclient
EOF

%clean
rm -rf %{buildroot}

%post -n dkms-%{name}
dkms add     -m %{name} -v %{version}-%{release} --rpm_safe_upgrade
dkms build   -m %{name} -v %{version}-%{release} --rpm_safe_upgrade
dkms install -m %{name} -v %{version}-%{release} --rpm_safe_upgrade

# rmmod any old driver if present and not in use (e.g. by X)
rmmod %{module_name} > /dev/null 2>&1 || true

%preun -n dkms-%{name}
dkms remove -m %{name} -v %{version}-%{release} --all --rpm_safe_upgrade

%files
%defattr(-,root,root)
%doc license.rtf license.txt sample.pcf README.urpmi
%{_bindir}/vpnclient
%{_bindir}/vpnclient.real
%{_bindir}/cisco_cert_mgr
%{_bindir}/ipseclog
%attr(4775,root,root) %{_bindir}/cvpnd
%{_libdir}/libvpnapi.so
%{_includedir}/vpnapi.h
%config(noreplace) %{_sysconfdir}/opt/cisco-vpnclient
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_sysconfdir}/bash_completion.d/%{name}
%{_var}/log/%{name}
/opt/cisco-vpnclient

%files -n dkms-%{name}
%defattr(-,root,root)
/usr/src/%{name}-%{version}-%{release}

%if %mdkversion < 200900
%post -p /sbin/ldconfig
%endif

%if %mdkversion < 200900
%postun -p /sbin/ldconfig
%endif

