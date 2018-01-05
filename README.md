![POLITICO](https://rawgithub.com/The-Politico/src/master/images/logo/badge.png)

# gspan

### What is this?

Gspan is a CLI that downloads an [anno-docs](https://github.com/nprapps/anno-docs)-formatted Google Doc and translates it into JSON.

### Quickstart

Gspan depends on [gdrive](https://github.com/prasmussen/gdrive) to handle downloading files from Google Drive. Install it with homebrew and authenticate your account:

```
$ brew install gdrive
$ gdrive list
```

Then, install gspan as a Python module.

```
$ pip install gspan
```

Then, you can use `gspan` as a command in your shell. To get JSON:

```
$ gspan parse <Google Doc ID> > output.json
```

As a principle, `gspan` pipes all of its output to stdout, much like [csvkit](http://csvkit.readthedocs.io/en/1.0.2/) and [elex](http://elex.readthedocs.io/en/stable/).

You can also download the raw Google Doc HTML and pipe that to a file:

```
$ gspan download <Google Doc ID> > download.html
```

### Testing

```
$ pytest
```
