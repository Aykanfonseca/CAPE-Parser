from bs4 import BeautifulSoup, SoupStrainer
import requests, time
from soc import main, unique_values

cape_url = 'http://cape.ucsd.edu/responses/Results.aspx?'
base_url = 'http://cape.ucsd.edu/responses/'

# Fromats each list item in list of lists.
def formatList (ls):
    # Gets rid of empty or useless lists.
    ls = [x[:7] for x in ls if x and (x != 'N/A') and 'detailedStats' not in x[0]]

    # Removes duplicate terms and keeps the first one found.
    ls = list(unique(ls))

    # Swaps term code with specific link to grade distributions, remove percentage signs, and deletes # enrolled.
    for item in ls:
        item[0], item[1] = item[1], item[0]
        del item[2]
        item[3] = item[3].partition(' ')[0]
        item[4] = item[4].partition(' ')[0]

    return ls

# Removes duplicates, preserves order, and keeps the first one you find.
def unique(ls):
    found = set()
    for item in ls:
        print item
        if item[1] not in found:
            yield item
            found.add(item[1])

# Returns the url with the data to parse by using a query string.
def updateQuery (value):
    value.replace(": ", " ")

    splitted = value.split()

    dept = splitted[0]
    num = splitted[1]

    # Pre formatted with %20.
    name = '%20'.join(splitted[2:])

    return ''.join([cape_url, 'courseNumber=', dept, '+', num, '&name=', name])

# Gets the specific data for each item in the list of lists.
def getSpecific (ls, headers):
    post = s.get(ls[1], headers=headers)
    strainer = SoupStrainer('div', attrs={'id' : 'ctl00_ContentPlaceHolder1_pnlGradesReceived'})

    # The text to search for info.
    text = BeautifulSoup(post.content, 'lxml', parse_only=strainer).text

    averages =  str(text.partition('Received:  ')[2].partition(')')[0]).split()

    try:
        # The letter grade average
        ls.append(averages[0])
        # The point average.
        ls.append(averages[2][1:])
    except IndexError:
        return []

    info = str(text.replace('%', ' ').partition('ABCDFPNP')[2]).split()
    del info[0]

    # Percentages of A, B, C, D, F, P, NP respectively.
    ls.extend(info)

    # Returns only complete data.
    return [x for x in ls if not 'N/A' in x]

# Parses the data from all of the terms and then delegates getting specific data to getSpecific().
def getOverview (URL, lname, dept):
    # User Agent to avoid 404 error.
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Gets the data.
    post = s.get(URL, headers=headers)
    soup = BeautifulSoup(post.content, 'lxml')
    td_elements = list(soup.findAll('td'))

    # No CAPEs for this professor.
    if 'No CAPEs have been submitted that match your search criteria.' in soup.text:
        return []

    # Parses the results.
    overview, term = [], []
    for item in td_elements:
        parsedText = str(' '.join(item.text.split()))

        # If the item is not the teacher, course, or averages received/expected.
        if (dept not in parsedText) and (lname not in parsedText) and ('(' not in parsedText):
            term.append(parsedText)

            # If the item is the study hrs./wk (the last item we want) we append to overview.
            if ('.' in parsedText) and not ('%' in parsedText):
                overview.append(term)

        # If the item is a hyperlink to the specific details, store it and start a new term list.
        try:
            anchor = item.find('a')['href']
        except:
            anchor = ""

        if anchor:
            term = []
            term.append(base_url + str(anchor))

    # formats the list of lists.
    overview = formatList(overview)

    result = []
    for item in overview:
        data = getSpecific(item, headers)
        if data != []:
            result.append(data)

    return result

# Finds the average list of info based on previous items and inserts at 1st spot in list of lists.
def averageInsert (ls, url):
    # Defines the average list and inserts the first two elements.
    average = []
    average.append('Average')
    average.append(url)

    # Defines the variables.
    evals = 0
    rc = 0
    ri = 0
    hours = 0
    grade = 0
    a = 0
    b = 0
    c = 0
    d = 0
    f = 0
    p = 0
    np = 0

    # The number of classes taught.
    count = 0
    for item in ls:
        if len(item) != 15:
            del item
        else:
            evals += int(item[2])
            rc += round(float(item[3]), 2)
            ri += round(float(item[4]), 2)
            hours += round(float(item[5]), 2)
            grade += round(float(item[7]), 2)
            a += round(float(item[8]), 2)
            b += round(float(item[9]), 2)
            c += round(float(item[10]), 2)
            d += round(float(item[11]), 2)
            f += round(float(item[12]), 2)
            p += round(float(item[13]), 2)
            np += round(float(item[14]), 2)
            count += 1

    average.append(str(evals))
    average.append(str(round(float(rc / count), 2)))
    average.append(str(round(float(ri / count), 2)))
    average.append(str(round(float(hours / count), 2)))
    x = round(float(grade / count), 2)

    if (x > 3.7):
        y = 'A-'
    elif (x > 3.3):
        y = 'B+'
    elif (x > 3.0):
        y = 'B'
    elif (x > 2.7):
        y = 'B-'
    elif (x > 2.3):
        y = 'C+'
    elif (x > 2.0):
        y = 'C'
    elif (x > 1.7):
        y = 'C-'
    elif (x > 1.0):
        y = 'D'
    else:
        y = 'F'

    average.append(str(y))
    average.append(str(x))
    average.append(str(round(float(a / count), 2)))
    average.append(str(round(float(b / count), 2)))
    average.append(str(round(float(c / count), 2)))
    average.append(str(round(float(d / count), 2)))
    average.append(str(round(float(f / count), 2)))
    average.append(str(round(float(p / count), 2)))
    average.append(str(round(float(np / count), 2)))

    # Inserts average list into the first spot.
    ls.insert(0, average)

    # Gets rid of empty or useless lists.
    return [x for x in ls if x]

if __name__ == '__main__':
    # Starts the timer.
    start = time.time()

    # Request session.
    s = requests.Session()

    items = unique_values(main())

    final = []
    for item in items:
        if 'Blank' in item:
            item.replace("Blank ","")

        if ('Staff ' not in item) and ('Blank' not in item):
            URL = updateQuery(item)

            dept = item.partition(":")[0].partition(" ")[2].strip()

            lname = item.partition(",")[0].partition(":")[2].strip()

            data = getOverview(URL, lname, dept)

            if data:
                final.append(averageInsert(data, URL))

    '''Format: Term, URL, Evals, Recommend Class %, Recommend Instructor, Study hrs. week, Average Letter Grade Received, Average Grade Point Received, Percentage of As, Percentage of Bs, Percentage of Cs, Percentage of Ds, Percentage of Fs, Percentage of Ps (Pass), Percentage of NPs (No Pass)'''

    for item in final:
        print item
        print '\n'

    # Ends the timer.
    end = time.time()

    # Prints how long it took for program to run.
    print('\n' + str(end - start))
