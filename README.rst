**********
Foobartory
**********

.. image:: https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-blue?logo=python&logoColor=white
   :target: https://www.python.org/downloads/release
   :alt: Python3.6+ compatible

.. image:: https://img.shields.io/readthedocs/foobartory?logo=read-the-docs
    :target: http://foobartory.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/github/workflow/status/thomasperrot/foobartory/CI?logo=github
   :target: https://github.com/thomasperrot/foobartory/actions?workflow=tests
   :alt: Continuous Integration Status

.. image:: https://codecov.io/gh/thomasperrot/foobartory/branch/master/graph/badge.svg?logo=codecov
   :target: https://codecov.io/gh/thomasperrot/foobartory
   :alt: Coverage Status

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :target: https://github.com/thomasperrot/foobartory/blob/master/LICENSE.rst
   :alt: MIT License

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style black


An actor model to simulate an automated production chain using Python asyncio_.

.. _asyncio: https://docs.python.org/fr/3/library/asyncio.html

Here's an example

.. image:: assets/example.gif
  :width: 700
  :alt: The foobartory CLI

Quickstart
**********

.. code-block:: bash

   $ python setup.py install

Once you have installed the package, you can run the Foobartory with the following options:

.. code-block::

   $ foobartory --speed=10 -v

To have details about the available options:

.. code-block::

   $ foobartory --help
   Usage: foobartory [OPTIONS]

   Options:
     -s, --speed FLOAT  Fasten the factory by the given factory (1 by default)
     -v, --verbose      Use multiple times to increase verbosity  [x>=0]
     --help             Show this message and exit.


Improvements
************

I chose to implement this project using Python asyncio. This is a simple and efficient approach, but
it could be improved. In particular, a major improvement would be to use a **micro-services**
architectures, where each robot is an independent process. The project would then follow
the following architecture:

* Each robot is an independent process, that would run synchronous Python code, packaged in Docker_.
* The factory is also an independent process, running synchronous Python code in Docker_.
* Each robot sends ``Foo``, ``Bar``,  ``FooBar`` and cash to RabbitMQ_ independent exchanges. Those four exchanges each have a unique queue, which is listen by all robots.
* When a robot wants to buy a new robot, it sends a message in a RabbitMQ_ exchange to inform the factory. This exchange is common to all robots, and have a single unique queue, which is listen only by the factory.
* The Factory is an independent process that is in charge of:
   * starting new robots. To do this,
   * stopping robots once 30 robots have been bought. To do this, the Factory sends a stop message to a dedicated exchange, which has one queue per robot. Every robot must stop when a message is received on that queue.

.. _Docker: https://www.docker.com/
.. _Redis lock: https://redis.io/topics/distlock
.. _RabbitMQ: https://www.rabbitmq.com/

.. Below this line is content specific to the README that will not appear in the doc.
.. end-of-index-doc

Where to go from here
---------------------

The complete docs_ is probably the best place to learn about the project.

If you encounter a bug, or want to get in touch, you're always welcome to open a
ticket_.

.. _docs: http://foobartory.readthedocs.io/en/latest
.. _ticket: https://github.com/thomasperrot/foobartory/issues/new