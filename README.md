## scraper for free parking places

to build an historical archive!

![sample curve](./sample-curve.png)

This is just a simple scraper. It takes web-sites or api endpoints and collects json-compatible data
which is then stored to json files with the filename being the timestamp. 


## Run
```shell script
python main.py store
```

to store a snapshot of each data source in the `./snapshot/` directory.

Any error will be written to the `./errors/` directory.


## Add new websites 
to `./sources/` and test/develop via

```shell script
python main.py dump -i my-new-source --cache
```

Run the `store` script regularly on a server and call

```shell script
rsync -avz -L -e 'ssh -p PORT' USER@SERVER:/PATH/parking-scraper/snapshots .
```
to update your local `snapshots` directory.

For disk-space reasons, a `DataSource` instance should store minimal necessary info and throw any meta-info away. 
For example, it should not store a complete geojson file, just the names and free spaces of each parking lot.

Each `DataSource` can implement a `transform_snapshot_data` function that transforms a snapshot into *cononical* 
data that has the same format for each parking place and can be exported via `python main.py load` 

## Access data

through `util.Storage` and `util.DataSources` (see `./notebooks/`). or via

```shell script
python main.py load
```
