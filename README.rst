|logo| Girder |license-badge|
=============================

**Data Management Platform**

Girder is a free and open source web-based data management platform developed by
`Kitware <https://kitware.com>`_ as part of the `Resonant <http://resonant.kitware.com>`_
data and analytics ecosystem.

|kitware-logo|

Documentation of the Girder platform can be found at
https://girder.readthedocs.io.

For questions, comments, or to get in touch with the maintainers, head to our `Discourse forum <https://discourse.girder.org>`_, or use our `Gitter Chatroom
<https://gitter.im/girder/girder>`_.

We'd love for you to `contribute to Girder <CONTRIBUTING.rst>`_.

Triggering deployment on dev
============================

Make sure you have a local copy with submodule initialized:

.. code::

    git clone --recurse-submodules -j4 git@github.com:whole-tale/girder.git

Steps to trigger a new build and a deployment @ ``.dev.wholetale.org``:

.. code::

    cd girder/plugins/wholetale  # or any other plugin that needs a bump
    git pull origin master
    cd ..
    git commit -a -m "Bump plugin (whole-tale/girder-wholetale#12345)"
    git push origin master

.. |logo| image:: clients/web/static/img/Girder_Favicon.png

.. |kitware-logo| image:: https://www.kitware.com/img/small_logo_over.png
    :target: https://kitware.com
    :alt: Kitware Logo

.. |license-badge| image:: docs/license.png
    :target: https://pypi.python.org/pypi/girder
    :alt: License

