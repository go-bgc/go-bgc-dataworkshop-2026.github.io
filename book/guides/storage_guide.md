# Code/Data Storage Guide

In general, the long-term persistence of any of the storage spaces listed below is not guaranteed. Make sure you backup all codes and data relevant to you as the workshop comes to an end. 

## JupyterHub environment filesystem

The filesystem of our JupyterHub environment provides various places for code/data storage. In particular,

+ The `shared` directory under the home directory (`/home/jovyan/shared`) is read-only and has a quota of 100 GB. This is the place where you'll find pre-loaded workshop tutorial/demo data. All participants have read-only access to this folder and see the same contents. If you believe that there are additional data that should be accessible to all participants, contact Wing-Ho Ko, who have write access to the folder.

+ The rest of the home directory (`/home/jovyan`, mapped as the root on JupyterLab file browsing panel) is accessible only by you and has a quota of 10 GB. This is a good place to store your codes and "small" datasets. This directory is persistent across different server instances.

+ The `/tmp` directory is accessible only by you and has a capacity of at least 100 GB. However, data on this directory is erased whenever the server is shutdown (either manually by you or automatically after some idle time). This directory can be useful for temporary data generated over the course of analysis.

## Amazon s3 bucket

In addition to storage space on the JupyterHub filesystem, all participants of the workshop also have access to the Amazon bucket s3://uw-escience-scratch-prod/. This bucket has essentially unlimited storage. 

Importantly, **all** participants have read and write permissions to **all** files on the bucket. As basic etiquette, do not erase other people's data. In addition, your data should always be stored inside a subfolder ("prefix" in Amazon S3 lingo). For your own data, use your GitHub username as the name of the subfolder (this is automatically set as the `SCRATCH_BUCKET` variable on your server). For project data, derive the subfolder name from the project name.

To read/write data on the bucket, you can either use the Terminal interface (via the `aws s3` command-line tool) or through python.

### Terminal interface

In the Terminal interface, you can use the `aws s3` command-line tool to manipulate files on the S3 bucket. The interface resembles somewhat the classic Linux file operation interface. In particular,

+ `aws s3 ls <remote_path>` lists the contents under a particular S3 path (note that the trailing slash (`/`) is required in this case).
+ `aws s3 cp <path_1> <path_2>` copies a file from path 1 (can be local or remote) to path 2 (can be local or remote).
+ `aws s3 mv <path_1> <path_2>` moves a file from path 1 (can be local or remote) to path 2 (can be local or remote).
+ `aws s3 rm <remote_path>` removes a file located at the specified S3 path
+ `aws s3 sync <path_1> <path_2>` recursively sync the files from the directory located at path 1 (can be local or remote) to the directory located at path 2 (can be local or remote).

For more information about the `aws s3` interface, consult the documentation at [https://docs.aws.amazon.com/cli/latest/reference/s3/](https://docs.aws.amazon.com/cli/latest/reference/s3/).

### Python interface

The python package `s3fs` can be used manipulate files on the S3 bucket. It provides both a pythonic interface (resembling the built-in `open()`) and Linux-like interface.

The first step for manipulating the S3 bucket is to start an S3 client:

```python
s3 = s3fs.S3FileSystem()
```

For the pythonic interface, just replace `open()` with `s3.open()`, e.g.,

```python
with s3.open(remote_url) as infile:
    data = infile.read()
```

or 

```python
with s3.open(remote_url, 'w') as outfile:
    outfile.write(data)
```

For the Linux-like interface, here are some useful functions:

+ `s3.ls(<path>)`: listing the contents of a s3 path.
+ `s3.put(<local>, <remote>)`: copy the local file from path `<local>` to the s3 path `<remote>`
+ `s3.get(<remote>, <local>)`: copy the remote s3 file `<remote>` to the local file at `<local>`
+ `s3.cp(<remote_1>, <remote_2>)`: copy remote s3 file at `<remote_1>` to the new s3 path `<remote_2>`
+ `s3.mv(<remote_1>, <remote_2>)`: move remote s3 file at `<remote_1>` to the new s3 path `<remote_2>`
+ `s3.rm(<remote>)`: delete remote s3 file at `<remote>`

Note that `s3.put()`, `s3.get()`, `s3.cp()`, `s3.mv()`, and `s3.ls()` all have an optional `recursive` argument that allows for manipulating multiple files at once.

For more information about `s3fs`, consult the documentation at [https://s3fs.readthedocs.io/en/latest/](https://s3fs.readthedocs.io/en/latest/)

In addition, note that some data science packages, including `pandas` and `xarray`, have native support of opening files on S3 bucket.