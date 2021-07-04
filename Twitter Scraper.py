#IMPORTING PYTHON LIBRARIES NEEDED FOR PROJECT

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from getpass import getpass
import pandas as pd
import re
import numpy as np

#LAUNCHING THE WEBDRIVER
driver = webdriver.Chrome() 
driver.maximize_window()

#LOG IN TO TWITTER 
#requesting for your login details
username_ = input('Username: ') #prompts you for username
password_ = getpass('Password: ') #prompts you for password

# LOGIN function 
def login(username=username_, password=password_):
    """takes two arguements username and pasword with default values set to your log-in details entered above;\
        it return None but successfully logs you into your twitter account via the chrome webdriver.
        NB: function applies sleep after every executable action to give driver allowance before performin the next action.
    """
    driver.get('https://twitter.com/login')
    sleep(5)
    log_in = driver.find_element_by_xpath('.//input[@name="session[username_or_email]"]')
    log_in.send_keys(username)
    sleep(2)
    password_ = driver.find_element_by_xpath('//input[@name="session[password]"]')
    password_.send_keys(password)
    sleep(2)
    password_.send_keys(Keys.RETURN)
    sleep(5)
    return 
login()

#SEARCHING FOR INTENDED KEYWORDS
search_ = input('Search word: ')  #prompts for the keyword
tab_ = input('Top/Latest ? : ')  #gets what category of tweet you need, i.e either Top or Latest

#SEARCH function
def search_func(search_word=search_, tab=tab_):
    """takes search_word and tab as arguement with defaults as prompted by the user above;
        returns None but navigates you to the search results page on twitter.
    """
    sleep(5)
    search = driver.find_element_by_xpath('.//input[@placeholder="Search Twitter"]')
    search.send_keys(search_word)
    sleep(2)
    search.send_keys(Keys.RETURN)
    sleep(2)
    driver.find_element_by_link_text(tab).click()
    sleep(3)
    return
search_func()


# GETTING TWEETS DATA

### card scraping data function
def card_scrap(card):
    """ takes a card from the twitter search result page and return a dictionary containing username, handle, 
        number of replies, retweets, and likes, tweet text, emoji and its title of a card been parsed.
    """
    username = card.find_element_by_xpath('./div[2]/div[1]//span').text          #stores username of card
    # a check for omitting sponsored tweets / ads 
    try:
        handle = card.find_element_by_xpath('.//span[contains(text(), "@")]').text
        date = card.find_element_by_xpath('.//time').get_attribute('datetime')
    except NoSuchElementException:
        return
    
    tweet = card.find_element_by_xpath('./div[2]/div[2]/div[1]').text            #stores tweet texts of card
    
    reply = card.find_element_by_xpath('.//div[@data-testid="reply"]').text      #stores number of tweet replies
    retweet = card.find_element_by_xpath('.//div[@data-testid="retweet"]').text  #stores number of retweets
    like = card.find_element_by_xpath('.//div[@data-testid="like"]').text        #stores number of likes
    
    emoji_list = []
    emoji_titles = []
    emoji_tags = card.find_elements_by_xpath('.//img[contains(@src, "emoji")]')
    #loops through all emoji img tags and extracts emoji titles and characters
    for emoji in emoji_tags:
        emojiLink = emoji.get_attribute('src')
        emoji_title = emoji.get_attribute('title') #gets the emoji title
        try:
            emoji = chr(int(re.search('/svg/([0-9a-z]+)\.svg', emojiLink).group(1), base=16)) #gets the emoji
        except AttributeError:
            continue
        if emoji:
            emoji_list.append(emoji)
        if emoji_title:
            emoji_titles.append(emoji_title)
    
    emojis = ' '.join(emoji_list)
    emojiTitles = ' '.join(emoji_titles)
        
    
    dict_ = {'USERNAME': username, 'HANDLE': handle, 'DATE': date,
             'TWEET': tweet, "REPLY COUNT": reply,
             'RETWEET COUNT': retweet, 'LIKE COUNT': like,
             'EMOJIS': emojis, 'EMOJI TITLES': emojiTitles}
    return dict_

### page scrolling while loop
scrolling  = True
cards_len = []                                                          #stores the number of cards on every scrolled page
lastHeight = driver.execute_script('return document.body.scrollHeight') #gets the last position before a scroll
scrolls = 0                                       #stores the total number of scrolls and initialized with 0 count

tweet_data = []   #store actual tweet data
tweet_ids = set() #stores the tweet ids to avoid replicas of tweets

#scroll loop: set a loop to keep scrolling until scrolling is set to False
while scrolling: 
    cards = driver.find_elements_by_xpath('.//div[@data-testid="tweet"]')  #gets all cards on each page
    cards_len.append(len(cards))   #gets the number of cards on each page and appends value to the cards_len
    
    for card in cards:
        tweet = card_scrap(card)
        if tweet:
            handle = tweet.get('HANDLE')
            date = tweet.get('DATE')
            tweet_ = tweet.get('TWEET')
            tweet_id = ''.join([handle, date, tweet_]) #uses the handle, date and tweet as unique identifier of each card scraped
            if tweet_id not in tweet_ids: 
                tweet_ids.add(tweet_id)
                tweet_data.append(tweet)
                
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);') #performs the scrolling operation
    scrolls+=1 
    sleep(5) #sleeps the loop for 5secs to allow page load completely
    newHeight = driver.execute_script('return document.body.scrollHeight') #takes the current position of the page
    checkScroll = 0 #a check for the number of scroll
    
    #scroll checking loop: checks if the the driver truly hits its final scroll
    while True:
        if lastHeight==newHeight:
            #breaks both while loops after 4 consecutive scrolls if page position remains same
            if checkScroll > 4: 
                scrolling = False
                break
            #keeps scrolling driver until the checkScroll exceeds 4 i.e maximum "scroll checking loop" is done 4 times
            else: 
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                checkScroll+=1  #adds 1 to total checkScroll,
                sleep(3)
                newHeight = driver.execute_script('return document.body.scrollHeight')
        #breaks "scroll checking loop" if pervious page height is not same as current page height
        else: 
            lastHeight = newHeight
            break

#closing the driver.
driver.close()


# SAVING TWEET DATA

### using the pandas library's .to_csv() method
username = []
handle = []
datetime = []
text = []
emoji =  []
emoji_titles = []
likes = []
retweets = []

###loops through tweet data and stores all data in their appropriate category.
for data in tweet_data:
    username.append(data.get('USERNAME'))
    handle.append(data.get('HANDLE'))
    datetime.append(data.get('DATE'))
    text.append(data.get('TWEET'))
    emoji.append(data.get('EMOJIS'))
    emoji_titles.append(data.get('EMOJI TITLES'))
    likes.append(data.get('LIKE COUNT'))
    retweets.append(data.get('RETWEET COUNT'))

###create a dataframe of the tweet data
final_data = pd.DataFrame({'UserName': username, 'Handle': handle, 'DateTime': datetime, 
                           'Text': text, 'Emoji': emoji, 'EmojiTitles': emoji_titles, 
                           'Likes': likes, 'Retweets': retweets})



#SAVING THE DATAFRAME INTO A CSV FILE.
filename = input('Prefered name of file to save data: ')
filename = str(filename+'.csv')

final_data.to_csv(filename)

print(f'DATA SUCCESSFULLY EXTRACTED AND SAVED IN {filename}')