# ispider_core

# V0.1

### Help
Show all the options
```
python3 run.py --help
```

### Crawl - PIPELINE STEP 1
You can specify a input file with the full path. File must contains the field ***domain*** (if no protocol specified, https will be used as default)
```
python3 run.py --crawl -file commons/inputs/size_report_urls.csv
```
You can specify a input file in the **commons/input** folder
```
python3 run.py --crawl -file size_report_urls.csv
```

You can specify one url, with or without the protocol (https://)
```
python3 run.py --crawl -one 'capitolawatches.com'
```
You can specify a subfolder to dump all file. 
Everything will be saved in dumps/xxx and will be available and independent from other subfolders
```
python3 run.py --crawl -file FILE -sub-folder SUBFOLDER
```

This is a working command used on the server, for v1.3
```
python3 -u run.py --crawl -file commons/inputs/shopify_100k.csv -pools 2 -proc 2 -dns-server 127.0.0.53
```

**Tested with more processes, faster, good in retrieving and retry/error corrections in v1.4**
```
python3 -u run.py --crawl -file commons/inputs/shopify_100k.csv -pools 16 -proc 16 -dns-server 127.0.0.53
```

### Parse
##### Parse ALL
Those script are configured to parse all and insert in DB, test or prod, depending on the script used
You can define the subfolder SUBFOLDER where to get the data
 - TEST
   - `./parse_test.sh SUBFOLDER`

 - PROD
   - `./parse_prod.sh SUBFOLDER`

##### PIPELINE STEP 2
This to create a report for the connections metadata
```
python3 run.py --parse -pools 24 -proc 24 conn
```
##### PIPELINE STEP 3
This to parse the landing page
```
python3 run.py --parse -pools 24 -proc 24 landing
```

##### PIPELINE STEP 4 - EMAILS
  0. *STAGE 0* 
  Extract all emails from html pages
  Create emails csv stage 0 in output, and st0 jsons in dump folder
    ```
    python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st0
    ```
  1. *STAGE 1* 
  From jsons produced by **st0**, 
  **group by email**, counts how many domains contains it
   produce csv in output and st1 jsons in the dump folder
    ```
    python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st1
    ```
  2. *STAGE 2* 
  From jsons produced by **st0**,
  **Email Classification**
   produce csv and st2 jsons
  **DNS Server needed for email_domain resolution**
    ```
    python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER -dns-server 127.0.0.53 emails-st2
    ```
  3. *STAGE 3* 
  From jsons produced by **st2**
  extract all usable emails (is_usable is True) 
  produce a csv and **st3** jsons
    ```
    python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st3
    ```
  4. *STAGE 4* 
  **DB Insert** 
    ```
    xtra='-sub-folder SUBFOLDER --just-emails'; python3 run.py $xtra dbdt; python3 run.py $xtra dbct; python3 run.py $xtra dbi;
    ```

To execute all stages:
```
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st-all
xtra='-sub-folder SUBFOLDER --just-emails'; python3 run.py $xtra dbdt; python3 run.py $xtra dbct; python3 run.py $xtra dbi;
```

##### PIPELINE STEP 5
```
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER socials
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER url-internal
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER url-sitemaps
```
##### PIPELINE STEP 6
Will join all the companies based on final_url_domain, shopid, etc
```
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER companies
```

#### PIPELINE STEP 7
Company Names St0
A funcPermNames = [
        removeNone, removeHyphen, removeQuote, removeSpace, removeDot, removeComma,
        removeEmojis, replaceUnidecode, 
        replaceAnd, replaceUnd, replaceY, removeAnd, 
        replaceSpecial
    ];
was used, 
and a "combination without repetition" function to call those functions on the 'site_name_cleaned' from the landing page, in the order specified (for the case of the &).

So when company_name_classification = 'cf_name_no_dots_no_spaces_no_comma_replace_special_dom_no_hyphen'
that means something like 
site_name_cleaned = 'Wel.do,ne s'a Cement™'
final_domain = "welldone-cement.com"

so in the string
-cf is always when match
-name_ it's everything related to name
-dom_ it's everything related to dom


##### PIPELINE STEP FINAL
### DB Insert
 - To recreate tables and insert all CSV in DB ***ecomm_test***
   ```
   python3 run.py dbdt; python3 run.py dbct; python3 run.py dbi; 
   ```

 - To insert all CSV in DB ***ecomm_prod***
   ```
   python3 run.py --prod dbdt; python3 run.py --prod dbct; python3 run.py --prod dbi;
   ```
 - To insert all CSV in DB ***ecomm_prod*** from some **SUBFOLDER**
   ```
   python3 run.py --prod dbdt; python3 run.py --prod dbct; python3 run.py -sub-folder --prod dbi;
   ```

# EXTRA FUNCTIONS
Check also the settings.py file for extra configuration, as 
 - proxy to be used
 - async block size
 - number of retries on error
 etc.

##### Help
```
python3 run.py --help
```
will show all the available options of the script

##### Pools and Procs
 - `-pools 4` 	will execute the script on 4 different cores, if available. Script will be spanned in 4 different processes
 - `-proc 4` 	number of workers, should be **always a multiple of pools** to correctly distribute the job against different pools

##### DNS Server
`-dns-server 141.1.1.1` This is a DNS server that will be used when IP is not retrievable by httpx module. UDP output needs to be opened

This is a normal execution on the *bigbadboy* server to retrieve DNS information, because outbound UDP against google dns are blocked
```
python3 -u run.py --crawl -file commons/inputs/shopify_100k.csv -pools 2 -proc 2 -dns-server 127.0.0.53
```
##### Proxy
`--force-proxy` it will force to use the proxy PROXY_TO_USE set up in *settings.py* file

##### Test
`--test` will scrape just a porcentage of the domains in input
The porcentage that will be scraped depend on the parameter PORCENTAGE_TO_SCRAPE_IN_TEST defined in *settings.py*

##### SUB_FOLDERS
`-sub-folder SUBFOLDER` will use a different configuration for
 - output folder
 - dump folder

For consistence, this flag must be specified in ***db insert*** too

### All pipeline
So, the whole pipeline will become
```
python3 -u run.py --crawl -file commons/inputs/shopify_100k.csv -pools 2 -proc 2 -dns-server 127.0.0.53 -sub-folder SUBFOLDER
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER conn
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER landings
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st0
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st1
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER -dns-server 127.0.0.53 emails-st2
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st3
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER socials
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER url-internal
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER url-sitemaps
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER companies-st0
python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER companies-st1
python3 run.py -sub-folder SUBFOLDER dbdt; python3 run.py -sub-folder SUBFOLDER dbct; python3 run.py -sub-folder SUBFOLDER dbi;
```


# HIGH LEVEL OPERATIONS
  ### EMAILS PIPELINE
  If you want to apply the complete pipeline just for **emails**, 
  it exists a flag --just-emails to apply to DB operations
  
  - STEP1, recreate the output
  ```
  python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st0
  python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st1
  python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER -dns-server 127.0.0.53 emails-st2
  python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER emails-st3
  ```
  - STEP2, recreate just the emails related tables: email_st0,email_st1,email_st2,email_st3
  ```
  xtra='-sub-folder SUBFOLDER --just-emails'; python3 run.py $xtra dbdt; python3 run.py $xtra dbct; python3 run.py $xtra dbi;
  ```

  ### COMPANIES
  If you want to apply the complete pipeline just for **companies**, 
  it exists a flag --just-companies to apply to DB operations
  
  1. recreate the output
  ```
  python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER companies-st0
  python3 run.py --parse -pools 24 -proc 24 -sub-folder SUBFOLDER companies-st1
  ```

  2. recreate just the emails related tables: email_st0,email_st1,email_st2,email_st3
  ```
  xtra='-sub-folder SUBFOLDER --just-companies'; python3 run.py $xtra dbdt; python3 run.py $xtra dbct; python3 run.py $xtra dbi;
  ```


  ### COMPANIES EXCLUSION 
  Create a table 'companies_exclusion' with an extra field set as "excluded" if some **domain_plus_tld** present in exclusion table based on **customer_id**
  To define exclusion table parameters, in settings.py
  - MYSQL_EXCLUSION_DB = 'customer'
  - MYSQL_EXCLUSION_TABLE = 'exclusion';
  - MYSQL_OUTPUT_COLUMN_CUSTOMER_ID = 'customer_id'
  - MYSQL_OUTPUT_COLUMN_DOMAIN_WITH_TLD = 'domain_cleaned'
  
  1. To run the script, this one **create a csv** file in output folder
  ```
  python3 -u run.py --parse -sub-folder 20230422  -customer-id **test** --exact companies-exclusion
  ```
  
  2. To **insert in DB**, 
  ```
  xtra='-sub-folder **20230422** --just-companies-exclusion'; python3 run.py $xtra dbdt; python3 run.py $xtra dbct; python3 run.py $xtra dbi;
  ```


## PARQUET FILE EXPORTER
- Under ecommerce_crawler/commons/scripts/parquets
- Search for parquets files under ecommerce_crawler/data/SUB-FOLDER/METHOD/files
- To select domains, accept in input *one file with full path*, file must be a csv and contains a domain column
  OR
- To select domains, Accept in input a *domain name part*, 

- Accept as input the **-sub-folder**, to specify the relative directory
- Accept as input the **method** (urls-st0 or urls-st1 ie)

`python3 pq.py -file inputs/all_woo_shopify_3k.csv -sub-folder ALL_WOO_GB urls-st0`
`python3 pq.py -file inputs/all_woo_shopify_3k.csv -sub-folder ALL_WOO_GB urls-st1`

`python3 pq.py -name-part "keys4" -sub-folder ALL_WOO_GB urls-st1`

- Output will be saved in ecommerce_crawler/commons/scripts/parquets/outputs
- Output will be saved on DB in a table name dependent of the method, as defined in settings
