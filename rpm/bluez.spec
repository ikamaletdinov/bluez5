Name:       bluez5

# >> macros
%define _system_groupadd() getent group %{1} >/dev/null || groupadd -g 1002 %{1}
# << macros

Summary:    Bluetooth daemon
Version:    5.43
Release:    1
Group:      Applications/System
License:    GPLv2+
URL:        http://www.bluez.org/
Source0:    http://www.kernel.org/pub/linux/bluetooth/%{name}-%{version}.tar.gz
Source1:    obexd-wrapper
Source2:    obexd.conf
Source3:    bluez.tracing
Source4:    obexd.tracing
Requires:   bluez5-libs = %{version}
Requires:   dbus >= 0.60
Requires:   hwdata >= 0.215
Requires:   bluez5-configs
Requires:   systemd
Requires:   oneshot
Requires(pre): /usr/sbin/groupadd
Requires(preun): systemd
Requires(post): systemd
Requires(postun): systemd
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(libusb)
BuildRequires:  pkgconfig(udev)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(check)
BuildRequires:  pkgconfig(libical)
BuildRequires:  bison
BuildRequires:  flex
BuildRequires:  readline
BuildRequires:  readline-devel
BuildRequires:  automake
BuildRequires:  autoconf
Conflicts: bluez

%description
%{summary}.

%package configs-mer
Summary:    Bluetooth (bluez5) default configuration
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}
Provides:   bluez5-configs
Conflicts:  bluez-configs-mer
%description configs-mer
%{summary}.

%package cups
Summary:    Bluetooth (bluez5) CUPS support
Group:      System/Daemons
Requires:   %{name} = %{version}-%{release}
Requires:   cups
Conflicts:  bluez-cups
%description cups
%{summary}.

%package doc
Summary:    Bluetooth (bluez5) daemon documentation
Group:      Documentation
Requires:   %{name} = %{version}-%{release}
Conflicts:  bluez-doc
%description doc
%{summary}.

%package hcidump
Summary:    Bluetooth (bluez5) packet analyzer
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}
Conflicts:  bluez-hcidump
%description hcidump
%{summary}.

%package libs
Summary:    Bluetooth (bluez5) library
Group:      System/Libraries
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig
Conflicts:  bluez-libs
%description libs
%{summary}.

%package libs-devel
Summary:    Bluetooth (bluez5) library development package
Group:      Development/Libraries
Requires:   bluez5-libs = %{version}
Conflicts:  bluez-libs-devel
%description libs-devel
%{summary}.

%package test
Summary:    Test utilities for Bluetooth (bluez5)
Group:      Development/Tools
Requires:   %{name} = %{version}-%{release}
Requires:   %{name}-libs = %{version}
Requires:   dbus-python
Requires:   pygobject2 >= 3.10.2
Conflicts:  bluez-test
%description test
%{summary}.

%package tools
Summary:    Command line tools for Bluetooth (bluez5)
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}
Conflicts:  bluez-tools
%description tools
%{summary}.

%package obexd
Summary:    OBEX server (bluez5)
Group:      System/Daemons
Requires:   %{name} = %{version}-%{release}
Requires:   obex-capability
Conflicts:  obexd
Conflicts:  obexd-server
%description obexd
%{summary}.

%package obexd-tools
Summary:    Command line tools for OBEX (bluez5)
Group:      Applications/System
%description obexd-tools
%{summary}.

%package tracing
Summary:    Configuration for bluez5 to enable tracing
Group:      Development/Tools
Requires:   %{name} = %{version}-%{release}
Conflicts:  bluez-tracing
%description tracing
Will enable tracing for BlueZ 5

%package obexd-tracing
Summary:    Configuration for bluez5-obexd to enable tracing
Group:      Development/Tools
%description obexd-tracing
Will enable tracing for BlueZ 5 OBEX daemon

%prep
%setup -q -n %{name}-%{version}/bluez

./bootstrap

%build
autoreconf --force --install

%configure \
    --enable-option-checking \
    --enable-library \
    --enable-sixaxis \
    --enable-test \
    --with-systemdsystemunitdir=/lib/systemd/system \
    --with-systemduserunitdir=/usr/lib/systemd/user \
    --enable-jolla-dbus-access \
    --enable-jolla-did \
    --enable-jolla-logcontrol \
    --with-phonebook=sailfish \
    --with-contentfilter=helperapp \
    --enable-jolla-blacklist \
    --disable-hostname

make %{?jobs:-j%jobs}

%check
# run unit tests
#make check

%install
rm -rf %{buildroot}
# >> install pre
# << install pre
%make_install

# >> install post

# bluez systemd integration
mkdir -p $RPM_BUILD_ROOT/%{_lib}/systemd/system/network.target.wants
ln -s ../bluetooth.service $RPM_BUILD_ROOT/%{_lib}/systemd/system/network.target.wants/bluetooth.service
(cd $RPM_BUILD_ROOT/%{_lib}/systemd/system && ln -s bluetooth.service dbus-org.bluez.service)

# bluez runtime files
install -d -m 0755 $RPM_BUILD_ROOT/%{_localstatedir}/lib/bluetooth

# bluez configuration
mkdir -p ${RPM_BUILD_ROOT}%{_sysconfdir}/bluetooth
for CONFFILE in profiles/input/input.conf profiles/network/network.conf profiles/proximity/proximity.conf src/main.conf ; do
install -v -m644 ${CONFFILE} ${RPM_BUILD_ROOT}%{_sysconfdir}/bluetooth/`basename ${CONFFILE}`
done

mkdir -p %{buildroot}%{_sysconfdir}/tracing/bluez/
cp -a %{SOURCE3} %{buildroot}%{_sysconfdir}/tracing/bluez/

# obexd systemd/D-Bus integration
(cd $RPM_BUILD_ROOT/%{_libdir}/systemd/user && ln -s obex.service dbus-org.bluez.obex.service)

# obexd wrapper
install -m755 -D %{SOURCE1} ${RPM_BUILD_ROOT}/%{_libexecdir}/obexd-wrapper
install -m644 -D %{SOURCE2} ${RPM_BUILD_ROOT}/%{_sysconfdir}/obexd.conf
sed -i 's,Exec=.*,Exec=/usr/libexec/obexd-wrapper,' \
    ${RPM_BUILD_ROOT}/%{_datadir}/dbus-1/services/org.bluez.obex.service
sed -i 's,ExecStart=.*,ExecStart=/usr/libexec/obexd-wrapper,' \
${RPM_BUILD_ROOT}/%{_libdir}/systemd/user/obex.service

# obexd configuration
mkdir -p ${RPM_BUILD_ROOT}/%{_sysconfdir}/obexd/{plugins,noplugins}

# HACK!! copy manually missing tools
cp -a ../bluez/tools/bluetooth-player %{buildroot}%{_bindir}/
cp -a ../bluez/tools/btmgmt %{buildroot}%{_bindir}/
cp -a ../bluez/attrib/gatttool %{buildroot}%{_bindir}/
cp -a ../bluez/tools/obex-client-tool %{buildroot}%{_bindir}/
cp -a ../bluez/tools/obex-server-tool %{buildroot}%{_bindir}/
cp -a ../bluez/tools/obexctl %{buildroot}%{_bindir}/

# HACK!! copy manually missing test scripts
cp -a ../bluez/test/exchange-business-cards %{buildroot}%{_libdir}/bluez/test/
cp -a ../bluez/test/get-managed-objects %{buildroot}%{_libdir}/bluez/test/
cp -a ../bluez/test/get-obex-capabilities %{buildroot}%{_libdir}/bluez/test/
cp -a ../bluez/test/list-folders %{buildroot}%{_libdir}/bluez/test/
cp -a ../bluez/test/simple-obex-agent %{buildroot}%{_libdir}/bluez/test/

mkdir -p %{buildroot}%{_sysconfdir}/tracing/obexd/
cp -a %{SOURCE4} %{buildroot}%{_sysconfdir}/tracing/obexd/
# << install post

%pre
%_system_groupadd bluetooth

%preun
if [ "$1" -eq 0 ]; then
systemctl stop bluetooth.service ||:
fi

%post
%{_bindir}/groupadd-user bluetooth
systemctl daemon-reload ||:
systemctl reload-or-try-restart bluetooth.service ||:

%postun
systemctl daemon-reload ||:

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig


%preun obexd
if [ "$1" -eq 0 ]; then
systemctl-user stop obex.service ||:
fi

%post obexd
systemctl-user daemon-reload ||:
systemctl-user reload-or-try-restart obex.service ||:

%postun obexd
systemctl-user daemon-reload ||:

%files
%defattr(-,root,root,-)
# >> files
%{_libexecdir}/bluetooth/bluetoothd
%{_libdir}/bluetooth/plugins/sixaxis.so
%{_datadir}/dbus-1/system-services/org.bluez.service
/%{_lib}/systemd/system/bluetooth.service
/%{_lib}/systemd/system/network.target.wants/bluetooth.service
/%{_lib}/systemd/system/dbus-org.bluez.service
%config %{_sysconfdir}/dbus-1/system.d/bluetooth.conf
# << files

%files configs-mer
%defattr(-,root,root,-)
# >> files configs-mer
%config %{_sysconfdir}/bluetooth/*
# << files configs-mer

%files cups
%defattr(-,root,root,-)
# >> files cups
%{_libdir}/cups/backend/bluetooth
# << files cups

%files doc
%defattr(-,root,root,-)
# >> files doc
%doc %{_mandir}/man1/*.1.gz
%doc %{_mandir}/man8/*.8.gz
# << files doc

%files hcidump
%defattr(-,root,root,-)
# >> files hcidump
%{_bindir}/hcidump
# << files hcidump

%files libs
%defattr(-,root,root,-)
# >> files libs
%{_libdir}/libbluetooth.so.*
# << files libs

%files libs-devel
%defattr(-,root,root,-)
# >> files libs-devel
%{_libdir}/libbluetooth.so
%dir %{_includedir}/bluetooth
%{_includedir}/bluetooth/*
%{_libdir}/pkgconfig/bluez5.pc
# << files libs-devel

%files test
%defattr(-,root,root,-)
# >> files test
%{_libdir}/bluez/test/*
# << files test

%files tools
%defattr(-,root,root,-)
# >> files tools
%{_bindir}/bccmd
%{_bindir}/bluetooth-player
%{_bindir}/bluemoon
%{_bindir}/bluetoothctl
%{_bindir}/btmgmt
%{_bindir}/btmon
%{_bindir}/ciptool
%{_bindir}/gatttool
%{_bindir}/hciattach
%{_bindir}/hciconfig
%{_bindir}/hcitool
%{_bindir}/hex2hcd
%{_bindir}/l2ping
%{_bindir}/l2test
%{_bindir}/mpris-proxy
%{_bindir}/rctest
%{_bindir}/rfcomm
%{_bindir}/sdptool
/%{_lib}/udev/hid2hci
/%{_lib}/udev/rules.d/97-hid2hci.rules
# << files tools

%files obexd
%defattr(-,root,root,-)
# >> files obexd
%config %{_sysconfdir}/obexd.conf
%dir %{_sysconfdir}/obexd/
%dir %{_sysconfdir}/obexd/plugins/
%dir %{_sysconfdir}/obexd/noplugins/
%attr(2755,root,privileged) %{_libexecdir}/bluetooth/obexd
%{_libexecdir}/obexd-wrapper
%{_datadir}/dbus-1/services/org.bluez.obex.service
%{_libdir}/systemd/user/obex.service
%{_libdir}/systemd/user/dbus-org.bluez.obex.service
# << files obexd

%files obexd-tools
%defattr(-,root,root,-)
# >> files obexd-tools
%{_bindir}/obex-client-tool
%{_bindir}/obex-server-tool
%{_bindir}/obexctl
# << files obexd-tools

%files tracing
%defattr(-,root,root,-)
%dir %{_sysconfdir}/tracing/bluez
%config %{_sysconfdir}/tracing/bluez/bluez.tracing

%files obexd-tracing
%defattr(-,root,root,-)
%dir %{_sysconfdir}/tracing/obexd
%config %{_sysconfdir}/tracing/obexd/obexd.tracing
