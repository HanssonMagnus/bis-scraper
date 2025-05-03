# `scrape_bis` 🏛️
`scrape_bis` stands for "scrape Bank for International Settlements" and it is a Python
package to download and transform speeches from all central banks globally.

## Project Information
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://python.org)
[![View Dataset on Kaggle](https://img.shields.io/badge/View%20on-Kaggle-blue)](https://www.kaggle.com/datasets/magnushansson/central-bank-speeches)

## Updates

#### Update 2025-04-27
There has been a while since this code and dataset have been updated and I thought it
was about time. The Kaggle page has been updated with a new dataset and a short backlog
of additional functionality has been created.

#### Update 2022-03-02
After requests the code is made available for the data collection in my paper
[Evolution of topics in central bank speech communication](https://arxiv.org/abs/2109.10058).

The original dataset, used in the paper, and a newly scraped dataset (2022-03-02) containing
central bank speeches can be found at
[Kaggle](https://www.kaggle.com/magnushansson/central-bank-speeches).

## The scripts
`scrape_bis`:
Scrapes the BIS website for all central bank (118 institutions) speeches over the period 1997-today and
sorts the speeches into directories named as the institution in the meta data "extra title" from
the BIS webpage. It takes around `3h` to collect all the speeches and the total size of the directory
of pdfs is around `2.4G`.
The scraper run sequentially and thus does not hit the BIS server hard. I've not noticed any
request restrictions from the server.

`pdf_to_txt`:
Converts the pdf files into `.txt` files such that they can be processed and used in
NLP. It takes around `29min` to convert all the `.pdf` files to `.txt` files and the
size of the directory of `.txt`s is around `326M`.

The code can run on standard laptops with more than `2.5G` of disk space.

## Required software
Required:
- Python 3.
- Packages listed in `Pipfile`: `requests`, `beautifulsoup4`, and `textract`.

Optional:
- [Pipenv](https://pipenv.pypa.io/en/latest/)

For a short introduction to `Pipenv` see
[this blog post](https://magnushansson.xyz/blog_posts/software/2020-03-26-Pipenv).

## Run the scraper
Step 1:
Clone repo and cd into the directory,
```bash
git clone https://github.com/HanssonMagnus/scrape_bis.git
cd scrape_bis
```

Step 2:
Create a pipenv environment and install packages,
```bash
pipenv shell
pipenv install
```

Step 3:
Run the scraper,
```bash
cd source/0_scrape_bis
python main.py
```

Step 4:
Convert pdfs to txts,
```bash
cd ../1_pdf_to_txt
python pdf_to_txt.py
```

Note: Step 2 can be changed to any other virtual environment or simply installing the
required packages in `Pipfile` with `pip install`.

## Logs
The scripts create a directory, `logs`, where log files for the scripts are saved.
`logging_bis_scraper.log` collects all speeches that it fails to download (around `100`), together
with the URLs to the speeches such that it is possible to manually investigate or download them.
`logging_pdf_to_txt.log` collects the pdf files that the script was unable to convert into txt
files. When the scripts are done you can compare the pdf and txt directories that you are
interested in and if they differ significantly in number you can investigate it.

## How it works
The speeches are sorted on the web-based search engine by dates, e.g., the
speeches from 08 Jan 2020 are named:
```
    https://www.bis.org/review/r200108a.pdf
    https://www.bis.org/review/r200108b.pdf
    .
    .
    .
    https://www.bis.org/review/r200108e.pdf
```

Thus the URL is the same and the date is the same, but the last letter is changing. The scraper
scrapes all speeches by creating a `datelist` with all dates from 1997 (the first speech) to today
and downloading all speeches for each day (incrementing a, b, c and so on) until there are no more
files for that day (page not found).

## FAQ

#### Who created this repo?
That would be me, Magnus, and you can reach me at hansson.carl.magnus@gmail.com.

#### Are there datasets available scraped with `scrape_bis`?
If you want to use the data without scraping it yourself, you can find the dataset
"Central Bank Speeches" uploaded
at [Kaggle][https://www.kaggle.com/datasets/magnushansson/central-bank-speeches].

#### How can I cite `scrape_bis`?
If you use this package or data scraped with this package in a paper or report please
cite it. The citation details can be found in the [`CITATION.bib`](./CITATION.bib) file
in this repository.

#### How can I contribute?
All contributions to the project, such as code, documentation, bug reports, issues, and
research applications, are welcome. Please refer to the following guidelines:

Reporting Issues:
- Check if the issue has already been reported.
- Create a new issue with a clear title and description.

Submitting Changes:
- Fork the repository.
- Make your changes in a new git branch.
- Commit your changes with clear, descriptive commit messages.
- Push your branch to your fork and submit a pull request to the main project.

Coding Standards:
- Follow the coding style and standards used in the project.
- Include comments in your code where necessary.
- Write tests for new functionality.

Code of Conduct:
- Be respectful and inclusive.

#### What license is the project under?
GPL-3.0 license.

#### Does BIS have any data permissions?
[BIS Copyright and Permissions:](https://www.bis.org/terms_conditions.htm#Copyright_and_Permissions)
"Users may download, display, print out, photocopy or redistribute any BIS Material for
non-commercial purposes."

#### How can I show my support?
Leave a ⭐️ if this project helped you!
