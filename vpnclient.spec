%define name    vpnclient
%define version 4.8.00.0490
%define release %mkrel 6

Name:           %{name}
Version:        %{version}
Release:        %{release}
Summary:        Cisco VPN client
License:        Commercial
Group:          Utilities
URL:            http://www.cisco.com/en/US/products/sw/secursw/ps2308/index.html
Source0:        %{name}-linux-x86_64-%{version}-k9.tar.bz2
Source1:        %{name}.bash-completion
Patch0:         vpnclient-linux-2.6.19.diff
Patch1:         vpnclient-linux-2.6.22.diff
Requires:       kmod(cisco_ipsec)
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
Provides:   kmod(cisco_ipsec)
Requires(post):	dkms
Requires(preun): dkms

%description -n dkms-%{name}
Kernel module for %{name}.

%prep
%setup -q -n %{name}
%patch0 -p 1
%patch1 -p 1

%install
rm -rf %{buildroot}

install -d -m 755 %{buildroot}%{_bindir}
install -m 755 vpnclient cisco_cert_mgr ipseclog cvpnd %{buildroot}%{_bindir}

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
%ifarch x86_64 amd64 ppc64 sparc64
install -m 755 libdriver64.so %{buildroot}/usr/src/%{name}-%{version}-%{release}
%else
install -m 755 libdriver.so %{buildroot}/usr/src/%{name}-%{version}-%{release}
%endif
cat > %{buildroot}/usr/src/%{name}-%{version}-%{release}/dkms.conf <<'EOF'
PACKAGE_NAME="%{name}"
PACKAGE_VERSION="%{version}-%{release}"
DEST_MODULE_LOCATION="/kernel/net/ipv4"
BUILT_MODULE_NAME="cisco_ipsec"
MAKE="/bin/true && make KERNEL_SOURCES=$kernel_source_dir"
MODULES_CONF_ALIAS_TYPE="cipsec"
AUTOINSTALL="YES"
BUILD_MAX_KERNEL=2.6.23
EOF

cat > README.urpmi <<EOF
mandriva RPM specific notes

setup
-----
The setup used here differs from default one, to achieve better FHS compliance.
- no init script needed, kernel module is loaded on demand
- the binaries are in %{_bindir}, and only a symlink is provided under /opt, 
  as the client hardcode cvpnd location
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
%{_bindir}/cisco_cert_mgr
%{_bindir}/ipseclog
%attr(4775,root,root) %{_bindir}/cvpnd
%{_libdir}/libvpnapi.so
%{_includedir}/vpnapi.h
%config(noreplace) %{_sysconfdir}/opt/cisco-vpnclient
%{_sysconfdir}/bash_completion.d/%{name}
%{_var}/log/%{name}
/opt/cisco-vpnclient

%files -n dkms-%{name}
%defattr(-,root,root)
/usr/src/%{name}-%{version}-%{release}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

