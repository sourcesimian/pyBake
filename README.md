PyBake <!-- omit in toc -->
===

***Create single file standalone Python scripts with builtin frozen file system***

- [Purpose](#purpose)
- [Usage](#usage)
  - [Bake Script](#bake-script)
- [Advanced](#advanced)
  - [Tracebacks](#tracebacks)
  - [Inspection Server](#inspection-server)
  - [Content](#content)
  - [Frozen File Systems](#frozen-file-systems)
- [License](#license)

# Purpose
PyBake can bundle an entire Python project including modules and data files into a single Python file, to provide a "standalone executable" style utility. PyBake supports pure Python modules only, thus PyBakes are multi-platform.

PyBakes just run and don't need an installation so are a great way of rapidly distributing tooling or utility scripts, yet the development can still be done using a formal module hierarchy.

The intention of PyBake is to be lightweight and to remain pure Python. There are several other "standalone executable" Python projects, with differing options and capabilities:
* [PyInstaller](https://www.pyinstaller.org/)
* [py2exe](https://www.py2exe.org/)
* [cx_Freeze](https://marcelotduarte.github.io/cx_Freeze)
* [py2app](https://github.com/ronaldoussoren/py2app/blob/master/README.rst)




# Usage
The current usage idiom is to create a bake script that is run when you wish to produce a release of your utility.
## Bake Script
This bake script includes an optional header to provide version information and setup instructions. The footer is used to invoke the desired entry point. The footer can be
omitted should you wish your PyBake to simply act as a module that can be imported into other scripts, e.g.:
```
#!/usr/bin/env python3
from pybake import PyBake

HEADER = '''\
################################################################################
##  my-util - Helper for ...                                                  ##
##  Setup: Save this entire script to a file called "my-util.py".             ##
##         Make it executable, e.g.: `chmod +x ./my-util.py`.                 ##
##         Run `./my-util.py --help`                                          ##
##  Version:   0.1                                                            ##
################################################################################
'''

FOOTER = '''\
if __name__ == '__main__':                                                    ##
    from my_util.main import main                                             ##
    exit(main())                                                              ##
'''

pb = PyBake(HEADER, FOOTER)
import my_util
pb.add_module(my_util)

with open('./data.json', 'rt') as fh:
    pb.add_file(('my_util', 'data.json'), fh)

pb.write_bake('my-util.py')
```

Then just run `my-util.py`.

# Advanced
## Tracebacks
A PyBake maintains a full representation of source paths and line numbers in Tracebacks. So it is easy to track down the source of any unhandled exceptions. For example if there was a `KeyError` in `main.py` of your utility, the Traceback would appear as follows. The path points to the PyBake path, and then the path from the frozen filesystem is suffixed.
```
Traceback (most recent call last):
  File "/home/user/./my-util.py", line 132, in <module>
    exit(main())                                                              ##
  File "/home/user/./my-util.py/my_util/main.py", line 3, in main
KeyError: 'Oops!'
```

## Inspection Server
Sometimes you may want to inspect the contents of your PyBake. This can be done by running your PyBake with the `--pybake-server` argument. It will run a small HTTP server that serves on `localhost:8080`. Open your web browser to http://localhost:8080 from where you can browse the contents. An additional argument will be interpreted as a port.

This feature is also a good way to calm the minds of your more suspicious colleagues, who think you're up to something nefarious because you've "obfuscated" your code. And then after lunch they happily `apt-get` install some binary on their machine without first reading the machine code ¯\_(ツ)_/¯

## Content
The content of a PyBake is pure Python. However, if you glance at the source you might think that it is some form of executable. However, taking a closer look at the head will show, e.g.:
```
#!/usr/bin/env python3
################################################################################
##  my-util - Helper for ...                                                  ##
##  ...
################################################################################
_='''eJzVPGuT2kiSf6XDGxv2xPV6QTQ+MxHzAWSkRtB4gEYIeRwdSAIkkISmxUtszH+/zCqp9CrRjHf
```
Then many of lines of "garbage", e.g.:
```
MzsXtdQdhkOqRle/Myqqv77wg2r8cbg5JtI5/DdmvOIHv+B++fAz2ztFfxx/j9cFZb1ZH//DhfZRYq93
```
And the tail will show. e.g.:
```
...
WgtFLYPu09hG9EDwjGF8MG9ei/fHH9/8BdRTTUQ=='''
import binascii, json, zlib                                                   ##
_ = json.loads(zlib.decompress(binascii.a2b_base64(_))); exec(_[0], globals())##
if __name__ == '__main__':                                                    ##
    from my_util.main import main                                             ##
    exit(main())                                                              ##
###########################################################################END##
```
As you can see a PyBake is simply a very short Python script with a giant zlib compressed Base 64 encoded data structure assigned to a string called `-`.

## Frozen File Systems
As mentioned PyBake is pure Python and serves as a demonstration of the awesome builtin capabilities of the Python standard libraries. If you are interested to understand more, start reading the source in [launcher.py](./pybake/launcher.py) and follow the `DictFileSystem`.


# License

In the spirit of the Hackers of the [Tech Model Railroad Club](https://en.wikipedia.org/wiki/Tech_Model_Railroad_Club) from the [Massachusetts Institute of Technology](https://en.wikipedia.org/wiki/Massachusetts_Institute_of_Technology), who gave us all so very much to play with. The license is [MIT](LICENSE).
