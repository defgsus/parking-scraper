## scraper for free parking places

to build an historical archive!

Run
```shell script
python main.py store
```

to store a snapshot of each data source in the `./snapshot/` directory.

Add new websites and stuff to `./sources/` and test via

```shell script
python main.py dump -i my-new-source --cache
```