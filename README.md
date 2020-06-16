<h2 align="center">backup-to-cloud <font color="red">(alpha)</font></h2>
Simple app designed to upload backups to google drive. Settings are handled by a yml file and it's explained <a href="#settings"> here</a>.

## Settings

Settings must be placed in `.settings.yml`, written in [YAML](https://yaml.org/), in the root dir.

Each entry must be declared like this:

```yaml
name:
  type: <type>
  zip: true
  path: /etc/apache2/sites-available/*.conf
  zipname: sites-available.zip
  cloud_folder_id: <folder_id>
```

Explanation:

- **name**: the name of the entry. It is irrelevant, only representative.
- **type**: the entry type. Right now it can be `single-file` or `multiple-files`.
- **root-path**: if type is `single-file`, it represents the path of the file. If type is `multiple-files`, it represents the root folder where the sistem will start listing files.
- **filter**: if the type is `multiple-files`, this regex filter will be applied to every file located below `root-path`. The search it's recursively. For example, to select all pdf files, use `filter=.py`. By default is `'.'`, which is a regex for match anything. It is encouraged to check the regex before creating the first backup. To check the regex read [this](#check-regex).
- **zip**: only used if the type is `multiple-files`. If True, the files will be zipped and uploaded as a single file, rather than multiple files.
- **zipname**: only used if type is `multiple-files` and `zip` is True. In that case, it must be provided. It sets the zip name to upload to google drive. Note that as it is a zip file, the extension should be `zip`.
- **cloud_folder_id**: id of the folder to save the file(s) into. If is not present or is `null`, the files will be stored in the root folder (`Drive`). More info for folder's id [here](#get-folders-id).

### Examples:

Saves all files with `conf` extension and saves them as a zip with name `sites-available.zip`, in a specific folder.

```yaml
apache-config:
  type: folder
  zip: true
  path: /etc/apache2/sites-available/*.conf
  zipname: sites-available.zip
  cloud_folder_id: <folder_id>
```

Backup a specific file.

```yaml
specific-file:
  type: file
  path: /home/user/data.db
  cloud_folder_id: <folder_id>
```

## Check regex

You can test if the regex matches the files you want to backup by using the command check-regex:

```bash
$ python main.py check-regex "<root-path>" "<regex>"
```

If `root-path` contains spaces, quotes ("") must be used.

## Get folder's id

When opening the folder in the browser, the URL will look like `https://drive.google.com/drive/u/3/folders/<folder-id>`. The folder's id appears at the end of the URL. It contains letters (lowercase and uppercase), numbers and hyphens.
