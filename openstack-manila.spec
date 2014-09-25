%global with_doc %{!?_without_doc:1}%{?_without_doc:0}

Name:             openstack-manila
Version:          2014.2
Release:          0.2%{?dist}
Summary:          OpenStack Shared Filesystem Service

Group:            Applications/System
License:          ASL 2.0
# We're only incubated, so we're not on openstack.org.
# URL:              http://www.openstack.org/software/openstack-filesystem/
URL:              http://github.com/stackforge/manila
#Source0:          https://launchpad.net/manila/icehouse/2014.2/+download/manila-%{version}.tar.gz
Source0:          manila-2014.2.dev32.g5d54abf.tar.gz
Source1:          manila.conf
Source2:          manila.logrotate
Source3:          manila-dist.conf
Source4:          api-paste.ini

Source10:         openstack-manila-api.service
Source11:         openstack-manila-scheduler.service
Source12:         openstack-manila-share.service

Source20:         manila-sudoers

Patch01:          manila-2014.2-oslosphinx.patch

#
# patches_base=2013.2
#
#Patch0001: 0001-Ensure-we-don-t-access-the-net-when-building-docs.patch

BuildArch:        noarch
# XXX Although intltool pulls gettext, we still traceback with undeclared '_'
BuildRequires:    intltool
BuildRequires:    python-d2to1
BuildRequires:    python-oslo-sphinx
BuildRequires:    python-pbr
BuildRequires:    python-setuptools
BuildRequires:    python-sphinx

Requires:         openstack-utils
Requires:         python-manila = %{version}-%{release}

Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Requires(pre):    shadow-utils

# We pull the posix_ipc with Oslo's common lockutils.
Requires:         python-posix_ipc

%description
OpenStack Shared Filesystem Service (code-name Manila) provides services
to manage network filesystems for use by Virtual Machine instances.

%package -n       python-manila
Summary:          Python libraries for OpenStack Shared Filesystem Service
Group:            Applications/System

# Rootwrap in 2013.2 and later deprecates anything but sudo.
Requires:         sudo

Requires:         MySQL-python

Requires:         python-paramiko

Requires:         python-qpid
Requires:         python-kombu
Requires:         python-amqplib

Requires:         python-eventlet
Requires:         python-greenlet
Requires:         python-iso8601
Requires:         python-netaddr
Requires:         python-lxml
Requires:         python-anyjson
Requires:         python-cheetah
Requires:         python-suds

Requires:         python-sqlalchemy
Requires:         python-migrate

Requires:         python-paste-deploy
Requires:         python-routes
Requires:         python-webob

Requires:         python-keystoneclient
Requires:         python-neutronclient
Requires:         python-novaclient >= 1:2.15

Requires:         python-oslo-config >= 1:1.2.0
Requires:         python-oslo-db
Requires:         python-oslo-messaging >= 1.3.0-0.1.a9
Requires:         python-oslo-rootwrap
Requires:         python-oslo-utils

# We need pbr at runtime because it deterimines the version seen in API.
Requires:         python-pbr

Requires:         python-six >= 1.5.0

Requires:         python-babel
Requires:         python-lockfile

%description -n   python-manila
OpenStack Shared Filesystem Service (code-name Manila) provides services
to manage network filesystems for use by Virtual Machine instances.

This package contains the associated Python library.

%package -n       %{name}-share
Summary:          An implementation of OpenStack Shared Filesystem Service
Group:            Applications/System

Requires:         python-manila = %{version}-%{release}

Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units
Requires(pre):    shadow-utils

# The manila-share can create shares out of LVM slices.
Requires:         lvm2
# The manila-share runs testparm, smbd and aborts if it's missing.
Requires:         samba

%description -n   %{name}-share
OpenStack Shared Filesystem Service (code-name Manila) provides services
to manage network filesystems for use by Virtual Machine instances.

This package contains a reference implementation of a service that
exports shares, similar to a filer.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for OpenStack Shared Filesystem Service
Group:            Documentation

Requires:         %{name} = %{version}-%{release}

BuildRequires:    systemd-units
#BuildRequires:    graphviz

# Required to build module documents
BuildRequires:    python-eventlet
BuildRequires:    python-routes
BuildRequires:    python-sqlalchemy
BuildRequires:    python-webob
# while not strictly required, quiets the build down when building docs.
BuildRequires:    python-migrate, python-iso8601

%description      doc
OpenStack Shared Filesystem Service (code-name Manila) provides services
to manage network filesystems for use by Virtual Machine instances.

This package contains the associated documentation.
%endif

%prep
#setup -q -n manila-%{version}
%setup -q -n manila-2014.2.dev32.g5d54abf

%patch01 -p1
#patch0001 -p1

find . \( -name .gitignore -o -name .placeholder \) -delete

find manila -name \*.py -exec sed -i '/\/usr\/bin\/env python/{d;q}' {} +

# Remove the requirements file so that pbr hooks don't add it
# to distutils requires_dist config
rm -rf {test-,}requirements.txt tools/{pip,test}-requires

# We add REDHATCINDERVERSION/RELEASE with the pbr removal patch
sed -i s/REDHATCINDERVERSION/%{version}/ manila/version.py
sed -i s/REDHATCINDERRELEASE/%{release}/ manila/version.py

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# docs generation requires everything to be installed first
export PYTHONPATH="$( pwd ):$PYTHONPATH"

pushd doc

%if 0%{?with_doc}
SPHINX_DEBUG=1 sphinx-build -b html source build/html
# Fix hidden-file-or-dir warnings
rm -fr build/html/.doctrees build/html/.buildinfo
%endif

# Create dir link to avoid a sphinx-build exception
mkdir -p build/man/.doctrees/
ln -s .  build/man/.doctrees/man
SPHINX_DEBUG=1 sphinx-build -b man -c source source/man build/man
mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 build/man/*.1 %{buildroot}%{_mandir}/man1/

popd

# Setup directories
install -d -m 755 %{buildroot}%{_sharedstatedir}/manila
install -d -m 755 %{buildroot}%{_sharedstatedir}/manila/tmp
install -d -m 755 %{buildroot}%{_localstatedir}/log/manila

# Install config files
install -d -m 755 %{buildroot}%{_sysconfdir}/manila
install -p -D -m 640 %{SOURCE1} %{buildroot}%{_sysconfdir}/manila/manila.conf
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_datadir}/manila/manila-dist.conf
install -p -D -m 640 etc/manila/rootwrap.conf %{buildroot}%{_sysconfdir}/manila/rootwrap.conf
# XXX We want to set signing_dir to /var/lib/manila/keystone-signing,
# but there's apparently no way to override the value in api-paste.ini
# from manila.conf. So we keep a forked api-paste.ini around for now.
#install -p -D -m 640 etc/manila/api-paste.ini %{buildroot}%{_sysconfdir}/manila/api-paste.ini
install -p -D -m 640 %{SOURCE4} %{buildroot}%{_sysconfdir}/manila/api-paste.ini
install -p -D -m 640 etc/manila/policy.json %{buildroot}%{_sysconfdir}/manila/policy.json

# Install initscripts for services
install -p -D -m 644 %{SOURCE10} %{buildroot}%{_unitdir}/%{name}-api.service
install -p -D -m 644 %{SOURCE11} %{buildroot}%{_unitdir}/%{name}-scheduler.service
install -p -D -m 644 %{SOURCE12} %{buildroot}%{_unitdir}/%{name}-share.service

# Install sudoers
install -p -D -m 440 %{SOURCE20} %{buildroot}%{_sysconfdir}/sudoers.d/manila

# Install logrotate
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-manila

# Install pid directory
install -d -m 755 %{buildroot}%{_localstatedir}/run/manila

# Install rootwrap files in /usr/share/manila/rootwrap
mkdir -p %{buildroot}%{_datadir}/manila/rootwrap/
install -p -D -m 644 etc/manila/rootwrap.d/* %{buildroot}%{_datadir}/manila/rootwrap/

## Remove unneeded in production stuff
# XXX Drop from Manila once we know for sure none of this is needed.
#rm -f %{buildroot}%{_bindir}/cinder-debug
#rm -fr %{buildroot}%{python_sitelib}/cinder/tests/
#rm -fr %{buildroot}%{python_sitelib}/run_tests.*
#rm -f %{buildroot}/usr/share/doc/cinder/README*

%pre -n python-manila
getent group manila >/dev/null || groupadd -r manila
getent passwd manila >/dev/null || \
   useradd -r -g manila -G manila,nobody -d %{_sharedstatedir}/manila \
      -s /sbin/nologin -c "OpenStack Manila Daemons" manila

%post
%systemd_post %{name}-api.service
%systemd_post %{name}-scheduler.service

%preun
%systemd_preun %{name}-api.service
%systemd_preun %{name}-scheduler.service

%postun
%systemd_postun_with_restart %{name}-api.service
%systemd_postun_with_restart %{name}-scheduler.service

%post -n %{name}-share
%systemd_post %{name}-share.service

%preun -n %{name}-share
%systemd_preun %{name}-share.service

%postun -n %{name}-share
%systemd_postun_with_restart %{name}-share.service

%files
%{_bindir}/manila-api
%{_bindir}/manila-scheduler
%{_unitdir}/%{name}-api.service
%{_unitdir}/%{name}-scheduler.service
%{_mandir}/man1/manila*.1.gz

%defattr(-, manila, manila, -)
%dir %{_sharedstatedir}/manila
%dir %{_sharedstatedir}/manila/tmp

%files -n python-manila
%doc LICENSE

# Aww, this is awkward. The python-manila itself does not need or provide
# any configurations, but since it's the bracket package, there's no choice.
%dir %{_sysconfdir}/manila
%config(noreplace) %attr(-, root, manila) %{_sysconfdir}/manila/manila.conf
%config(noreplace) %attr(-, root, manila) %{_sysconfdir}/manila/api-paste.ini
%config(noreplace) %attr(-, root, manila) %{_sysconfdir}/manila/rootwrap.conf
%config(noreplace) %attr(-, root, manila) %{_sysconfdir}/manila/policy.json
%config(noreplace) %{_sysconfdir}/logrotate.d/openstack-manila
%config(noreplace) %{_sysconfdir}/sudoers.d/manila

%dir %{_datadir}/manila
%dir %{_datadir}/manila/rootwrap
%{_datadir}/manila/rootwrap/*
%attr(-, root, manila) %{_datadir}/manila/manila-dist.conf

# XXX On Fedora 19 and later, /var/run is a symlink to /run, which is mounted.
# If one specifies directories in /run, they disappear on reboot. Fix?
%dir %attr(0750, manila, root) %{_localstatedir}/log/manila
%dir %attr(0755, manila, root) %{_localstatedir}/run/manila

%{python_sitelib}/manila
%{python_sitelib}/manila-%{version}*.egg-info

%{_bindir}/manila-all
%{_bindir}/manila-manage
%{_bindir}/manila-rootwrap

%files -n %{name}-share
%{_bindir}/manila-share
%{_unitdir}/%{name}-share.service

%if 0%{?with_doc}
%files doc
%doc doc/build/html
%endif

%changelog
* Wed Sep 10 2014 Pete Zaitcev <zaitcev@redhat.com>
- 2014.2-0.2
- Address review comments bz#1125033 comment#2
- Upstream removed jQuery

* Sun Aug 10 2014 Pete Zaitcev <zaitcev@redhat.com>
- 2013.2-0.9
- Add dependency on python-neutronclient, else traceback
- Split away the openstack-manila-share and its dependencies on lvm2 and samba

* Wed Jul 30 2014 Pete Zaitcev <zaitcev@redhat.com>
- 2013.2-0.8
- Switch to dynamic UID/GID allocation per Packaging:UsersAndGroups

* Tue Jul 29 2014 Pete Zaitcev <zaitcev@redhat.com>
- 2013.2-0.7
- Require python-pbr after all

* Thu Jun 26 2014 Pete Zaitcev <zaitcev@redhat.com>
- 2013.2-0.3
- Initial testing RPM