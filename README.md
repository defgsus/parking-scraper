## scraper for free parking places

to build an historical archive!

This is just a simple scraper. It takes web-sites or api endpoints and collects json-compatible data
which is then stored to json files with the filename being the timestamp. 


Run
```shell script
python main.py store
```

to store a snapshot of each data source in the `./snapshot/` directory.

Any error will be written to the `./errors/` directory.


Add new websites and stuff to `./sources/` and test via

```shell script
python main.py dump -i my-new-source --cache
```

Run the `store` script regularly on a server and call

```shell script
rsync -avz -L -e 'ssh -p PORT' USER@SERVER:/PATH/parking-scraper/snapshots .
```
to update your local `snapshots` directory.