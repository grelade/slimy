from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException,WebDriverException,TimeoutException,StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests
import json
from time import sleep
import os

import slimy_locale
import config

def download(url,file_name=None):
    headers=headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    get_response = requests.get(url,stream=True, allow_redirects=True,headers=headers)
    if file_name == None:
        file_name  = url.split("/")[-1]
    else:
        file_name = file_name
    with open(file_name, 'wb') as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                
def speech2text(audio_file):
    API_TOKEN = config.SPEECH2TEXT_API
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    API_URL = config.SPEECH2TEXT_URL

    def query(filename):
        with open(filename, "rb") as f:
            data = f.read()
        response = requests.request("POST", API_URL, headers=headers, data=data)
        return json.loads(response.content.decode("utf-8"))

    data = query(audio_file)
    
    return data['text'] 

def retrieve_transcript(audio_url,rm_audio = True):
    audio_path = 'audio.mp3'
    download(audio_url,audio_path)
    text = speech2text(audio_path)
    if rm_audio:
        os.remove(audio_path)
    return text

class captcha_state:
    
    LANGS_DESC = slimy_locale.LANGS_DESC
    LANGS = slimy_locale.LANGS
    EXPIRED_MSGS = slimy_locale.EXPIRED_MSGS
    MAIN_IFRAME_TITLES = slimy_locale.MAIN_IFRAME_TITLES
    CAPTCHA_IFRAME_TITLES = slimy_locale.CAPTCHA_IFRAME_TITLES
    AUDIOCHALLENGE_MORE_MSGS = slimy_locale.AUDIOCHALLENGE_MORE_MSGS
    LIMIT_REACHED_MSGS = slimy_locale.LIMIT_REACHED_MSGS
    
#     LANGS = ['en']
#     EXPIRED_MSGS = ['Verification expired. Check the checkbox again.'] # before challenge presented
#     EXPIRED_MSGS += ['Verification challenge expired. Check the checkbox again.'] # after challenge presented
#     EXPIRED_MSGS += ['Verification challenge expired, check the checkbox again for a new challenge'] # other
#     EXPIRED_MSGS += ['Verification expired, check the checkbox again for a new challenge'] # other
#     MAIN_IFRAME_TITLES = ['reCAPTCHA']
#     CAPTCHA_IFRAME_TITLES = ['recaptcha challenge expires in two minutes']
    
#     AUDIOCHALLENGE_MORE_MSGS = ['Multiple correct solutions required - please solve more.']
#     LIMIT_REACHED_MSGS = ['Try again later']
    
    DEFAULT_TIMEOUT = 2
    
    def __init__(self,
                 driver: WebDriver,
                 focus_mode: str = 'slow',
                 verbose: bool = False):
        self.driver = driver
        
        self.EXISTS = False # does the captcha exist
        self.EXPIRED = False # has the captcha expired
        self.TICKED = False # is the captcha ticked (passed)
        self.CAPTCHA_FRAME = False # is captcha iframe displayed
        self.AUDIOCHALLENGE = False # is audio challenge div displayed
        self.AUDIOCHALLENGE_MORE = False # are more challenges required
        self.LIMIT_REACHED = False # is captcha limit reached
        
        # iframe objects for faster? navigation
        self.main_iframe = None
        self.main_iframe_title = None
        self.captcha_iframe = None
        self.captcha_iframe_title = None
        
        self.focus_mode = focus_mode
        self.verbose = verbose
        
    def identify_iframes(self,timeout=DEFAULT_TIMEOUT):

        try:
            if self.verbose: print(f'captcha_state._identify_iframes(): START')
            
            self.driver.switch_to.default_content()
            
            pair = (By.XPATH,"//iframe")
            iframes = WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located(pair))

            for iframe in iframes:
                iframe_title = iframe.get_property('title')
                for title in captcha_state.MAIN_IFRAME_TITLES:

                    if iframe_title == title:
                        self.main_iframe = iframe
                        self.main_iframe_title = title
                        if self.verbose: print(f'main iframe id: {self.main_iframe.id}')

                for title in captcha_state.CAPTCHA_IFRAME_TITLES:
                    # iframe_title = iframe.get_property('title')
                    if iframe_title == title:
                        self.captcha_iframe = iframe
                        self.captcha_iframe_title = title
                        if self.verbose: print(f'captcha iframe id: {self.captcha_iframe.id}')
                        
            if self.verbose: print(f'captcha_state._identify_iframes(): END')
            
        except Exception as e:
            if self.verbose: print(f'captcha_state._identify_iframes(): ERROR {e}')
            pass
        
        
    def _main_iframe_focus(self,timeout=DEFAULT_TIMEOUT):

        self.driver.switch_to.default_content()
        if self.focus_mode == 'slow':
            pair = (By.XPATH,f"//iframe[@title='{self.main_iframe_title}']")
            iframe = WebDriverWait(self.driver, timeout).until(EC.frame_to_be_available_and_switch_to_it(pair))
        elif self.focus_mode == 'fast':
            self.driver.switch_to.frame(self.main_iframe)  

    
    def main_iframe_focus(self,timeout=DEFAULT_TIMEOUT):
        try:
            if self.verbose: print('captcha_state.main_iframe_focus(): START')
            
            self._main_iframe_focus(timeout = timeout)
            
            if self.verbose: print('captcha_state.main_iframe_focus(): END')
            
        except Exception as e:
            if self.verbose: print(f'captcha_state.main_iframe_focus(): ERROR {e}')
            pass            
    
    def _captcha_iframe_focus(self,timeout=DEFAULT_TIMEOUT):
     
        self.driver.switch_to.default_content()
        if self.focus_mode == 'slow':
            pair = (By.XPATH,f"//iframe[@title='{self.captcha_iframe_title}']")
            iframe = WebDriverWait(self.driver, timeout).until(EC.frame_to_be_available_and_switch_to_it(pair))
        elif self.focus_mode == 'fast':
            self.driver.switch_to.frame(self.captcha_iframe)

    
    def captcha_iframe_focus(self,timeout=DEFAULT_TIMEOUT):
        try:
            if self.verbose: print(f'captcha_state.captcha_iframe_focus(): START')
            
            self._captcha_iframe_focus(timeout = timeout)
            
            if self.verbose: print(f'captcha_state.captcha_iframe_focus(): END')
            
        except Exception as e:
            if self.verbose: print(f'captcha_state.captcha_iframe_focus(): ERROR {e}')
            pass        
        
    
    def _check_exists(self,timeout=DEFAULT_TIMEOUT):
        try:
            self.driver.switch_to.default_content()
            
            pair = (By.XPATH,f"//iframe[@title='{self.main_iframe_title}']")
            iframe = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(pair))
            return True

        except:
            return False
        
    def update_exists(self,timeout=DEFAULT_TIMEOUT):
        self.EXISTS = self._check_exists(timeout)
        
    def _check_expired(self,timeout=DEFAULT_TIMEOUT):
        
        try:
            self._main_iframe_focus(timeout=timeout)
            
            pair = (By.CLASS_NAME,'rc-anchor-error-msg')
            out = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(pair))
            # out = driver.find_element(*pair)

            for msg in captcha_state.EXPIRED_MSGS:
                if out.text == msg:
                    return True
                                                            
            return False
                                                            
        except:                                              
            return False
        
    def update_expired(self,timeout=DEFAULT_TIMEOUT):
        self.EXPIRED = self._check_expired(timeout)
        
    def _check_ticked(self,timeout=DEFAULT_TIMEOUT):
        
        try:
            self._main_iframe_focus(timeout=timeout)
            
            pair = (By.CLASS_NAME,'recaptcha-checkbox-checked')
            out = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(pair))
            # out = driver.find_element(*pair)
                         
            return True
                                                            
        except:                                              
            return False
        
    def update_ticked(self,timeout=DEFAULT_TIMEOUT):
        self.TICKED = self._check_ticked(timeout)
        
    def _check_captcha_frame(self,timeout=DEFAULT_TIMEOUT):
        try:
            self.driver.switch_to.default_content()
            
            if self.focus_mode == 'slow':
                pair = (By.XPATH,f"//iframe[@title='{self.captcha_iframe_title}']")
                iframe =  WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(pair))
            elif self.focus_mode == 'fast':
                iframe = self.captcha_iframe
                
            if iframe.is_displayed():
                return True
            
            return False

        except:
            return False
        
    def update_captcha_frame(self,timeout=DEFAULT_TIMEOUT):
        self.CAPTCHA_FRAME = self._check_captcha_frame(timeout)
        
    def _check_audiochallenge(self,timeout=DEFAULT_TIMEOUT):
        try:
            self.driver.switch_to.default_content()
            if not self.captcha_iframe.is_displayed():
                return False
            
            self._captcha_iframe_focus(timeout=timeout)
            
            # pair = (By.CLASS_NAME,'rc-audiochallenge-tabloop-begin')
            pair = (By.CLASS_NAME,'rc-audiochallenge-tdownload')
            span =  WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(pair))
            # span = driver.find_element(*pair)
            if span.is_displayed():
                return True
            
            return False
        
        except:
            return False
    
    def update_audiochallenge(self,timeout=DEFAULT_TIMEOUT):
        self.AUDIOCHALLENGE = self._check_audiochallenge(timeout)
        
    def _check_audiochallenge_more(self,timeout=DEFAULT_TIMEOUT):
        try:
            self.driver.switch_to.default_content()
            if not self.captcha_iframe.is_displayed():
                return False
            self._captcha_iframe_focus(timeout=timeout)
            
            # pair = (By.CLASS_NAME,'rc-audiochallenge-tabloop-begin')
            pair = (By.CLASS_NAME,'rc-audiochallenge-error-message')
            div =  WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(pair))
            # span = driver.find_element(*pair)
            txt = div.text
            for msg in captcha_state.AUDIOCHALLENGE_MORE_MSGS:
                if txt == msg and div.is_displayed():
                    return True
                            
            return False
        
        except:
            return False
        
    def update_audiochallenge_more(self,timeout=DEFAULT_TIMEOUT):
        self.AUDIOCHALLENGE_MORE = self._check_audiochallenge_more(timeout)
        
    def _check_limit_reached(self,timeout=DEFAULT_TIMEOUT):
        try:
            self.driver.switch_to.default_content()
            if not self.captcha_iframe.is_displayed():
                return False
            self._captcha_iframe_focus(timeout=timeout)
            
            pair = (By.XPATH,"//div[@class='rc-doscaptcha-header-text']")
            header = WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located(pair))
            # header = self.driver.find_element(*pair)
            
            txt = header.text
            for msg in captcha_state.LIMIT_REACHED_MSGS:
                if txt == msg:
                    return True
            
            return False
        
        except:
            return False
        
    def update_limit_reached(self,timeout=DEFAULT_TIMEOUT):
        self.LIMIT_REACHED = self._check_limit_reached(timeout)
                
    def update_state(self):
        if self.verbose: print(f'captcha_state.update_state(): START')
        self.update_exists()
        self.update_expired()
        self.update_ticked()
        self.update_captcha_frame()
        self.update_audiochallenge()
        self.update_audiochallenge_more()
        self.update_limit_reached()
        if self.verbose: print(f'captcha_state.update_state(): END')
        
    def __str__(self):
        s = 'captcha_state\n'
        s += f'EXISTS: {self.EXISTS}\n'
        s += f'EXPIRED: {self.EXPIRED}\n'
        s += f'TICKED: {self.TICKED}\n'
        s += f'CAPTCHA_FRAME: {self.CAPTCHA_FRAME}\n'
        s += f'AUDIOCHALLENGE: {self.AUDIOCHALLENGE}\n'
        s += f'AUDIOCHALLENGE_MORE: {self.AUDIOCHALLENGE_MORE}\n'
        s += f'LIMIT_REACHED: {self.LIMIT_REACHED}\n'
        return s
    
    
# def noelement_exception(func):
#     def f(*args,**kwargs):
#         try:
#             return func(*args,**kwargs)
#         except NoSuchElementException as e:
#             print(f'{func.__name__}: NoSuchElementException : {e}')
#             return None
#     f.__name__ = func.__name__
#     return f

# def webdriver_exception(func):
#     def f(*args,**kwargs):
#         try:
#             return func(*args,**kwargs)
#         except WebDriverException as e:
#             print(f'{func.__name__}: WebDriverException : {e}')
#             return None
#     f.__name__ = func.__name__
#     return f

# def iframefail_exception(func):
#     def f(*args,**kwargs):
#         try:
#             return func(*args,**kwargs)
#         except StaleElementReferenceException as e:
#             print(f'{func.__name__}: StaleElementReferenceException : {e}')
#             return None
#     f.__name__ = func.__name__  
#     return f
    
# def timeout_exception(func):
#     def f(*args,**kwargs):
#         try:
#             return func(*args,**kwargs)
#         except TimeoutException as e:
#             print(f'{func.__name__}: TimeoutException : {e}')
#             return None
#     f.__name__ = func.__name__
#     return f

class captcha:
    
    DEFAULT_TIMEOUT = 5
    
    def __init__(self,
                 driver: WebDriver,
                 tries = 5,
                 verbose: bool = False):
        
        self.driver = driver
        self.tries = tries
        self.verbose = verbose
        
        self.cstate = captcha_state(self.driver,
                                    verbose=self.verbose)
        self.cstate.identify_iframes()
        self.audio_module = captcha_audio(self)

    def click_norobot(self,timeout=DEFAULT_TIMEOUT):
        try:
            if self.verbose: print('captcha._click_norobot(): START')
            
            path = (By.XPATH,"//span[@id='recaptcha-anchor']")
            norobot = WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located(path))
            norobot.click()
            
            if self.verbose: print('captcha._click_norobot(): END')
            
            return True
        
        except Exception as e:
            if self.verbose: print(f'captcha._click_norobot(): ERROR {e}')
            return False
    
    def pass_captcha(self):
        try:
            self.cstate.update_state()

            if self.cstate.EXISTS:
                if self.verbose: print('captcha.pass_captcha(): captcha found!')

                for i in range(5):
                    if self.verbose: print(f'captcha.pass_captcha(): route search {i} attempt')
                    # prepare
                    self.cstate.main_iframe_focus()
                    
                    if not self.cstate.CAPTCHA_FRAME:
                        success = self.click_norobot()

                        if success:
                            self.cstate.update_state()

                    if self.cstate.TICKED:
                        if self.verbose: print('captcha.pass_captcha(): route NO-CHECK; ending search')
                        break
                    
                    if self.cstate.CAPTCHA_FRAME:
                        if self.verbose: print('captcha.pass_captcha(): route AUDIO')
                        success = self.audio_module.run()
                        # if self.verbose: print('func: audio_module.run()')

                        if not success:
                            if self.verbose: print('captcha.pass_captcha(): AUDIO failed; repeating route search')

                    elif self.cstate.EXPIRED:
                        if self.verbose: print('captcha.pass_captcha(): route EXPIRED; repeating route search')

                    else:
                        if self.verbose: print('captcha.pass_captcha(): route UNKNOWN; repeating route search')

                # check success
                self.cstate.update_state()    

                if self.cstate.TICKED:
                    if self.verbose: print('captcha.pass_captcha(): captcha success!')
                    return True
                else:
                    if self.verbose: print('captcha.pass_captcha(): no captcha success...')
                    return False              
            else:
                if self.verbose: print('captcha.pass_captcha(): no captcha found !')
                return False
        
        except:
            return False

class captcha_audio:
    
    DEFAULT_TIMEOUT = 5
    
    def __init__(self,captcha_instance: captcha):
        
        self.captcha = captcha_instance
        self.driver = self.captcha.driver
        self.cstate = self.captcha.cstate
        self.tries = self.captcha.tries
        self.verbose = self.captcha.verbose
        
    def click_reload(self,timeout=DEFAULT_TIMEOUT):
        try: 
            if self.verbose: print('captcha_audio.click_reload(): START')
            
            self.cstate._captcha_iframe_focus()

            pair = (By.XPATH,"//button[@id='recaptcha-reload-button']")
            reloadbutton = WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located(pair))
            reloadbutton.click()
            sleep(1)
            
            if self.verbose: print('captcha_audio.click_reload(): END')
            
        except Exception as e:
            if self.verbose: print(f'captcha_audio.click_reload(): ERROR {e}')
            pass

    def click_audio(self,timeout=DEFAULT_TIMEOUT):
        try:
            if self.verbose: print('captcha_audio.click_audio(): START')
            
            self.cstate._captcha_iframe_focus()

            pair = (By.XPATH,"//button[@id='recaptcha-audio-button']")
            audiobutton = WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located(pair))
            audiobutton.click()
            sleep(1)
            
            if self.verbose: print('captcha_audio.click_audio(): END')
        
        except Exception as e:
            if self.verbose: print(f'captcha_audio.click_reload(): ERROR {e}')
            pass

    def find_audio_url(self,timeout=DEFAULT_TIMEOUT):
        try:
            if self.verbose: print('captcha_audio.find_audio_url(): START')
            
            self.cstate._captcha_iframe_focus()

            pair = (By.CLASS_NAME,'rc-audiochallenge-tdownload-link')
            a = WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located(pair))
            audio_url = a.get_property('href')
            
            if self.verbose: print('captcha_audio.find_audio_url(): END')
            return audio_url
        
        except Exception as e:
            if self.verbose: print('captcha_audio.find_audio_url(): ERROR {e}')
            pass


    def input_transcript(self,text,timeout=DEFAULT_TIMEOUT):
        try:
            if self.verbose: print('captcha_audio.input_transcript(): START')
            
            self.cstate._captcha_iframe_focus()

            pair = (By.ID,'audio-response')
            text_input = WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located(pair))
            # text_input = self.driver.find_element(*pair)
            text_input.send_keys(text)
            
            if self.verbose: print('captcha_audio.input_transcript(): END')
        
        except Exception as e:
            if self.verbose: print('captcha_audio.input_transcript(): ERROR {e}')
            pass
        
    def click_verify(self,timeout=DEFAULT_TIMEOUT):
        try:
            if self.verbose: print('captcha_audio.click_verify(): START')
            
            self.cstate._captcha_iframe_focus()
        
            pair = (By.ID,'recaptcha-verify-button')
            verify_button = WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located(pair))
            # verify_button = self.driver.find_element(*pair)
            verify_button.click()
            sleep(1)
            
            if self.verbose: print('captcha_audio.click_verify(): END')
            
        except Exception as e:
            if self.verbose: print('captcha_audio.click_verify(): ERROR {e}')
            pass

        
    def run(self):
        
        # audio_check_route logic
        self.cstate.captcha_iframe_focus()
        
        for i in range(5):
            
            # self.click_reload()
            self.click_audio()
            self.cstate.update_state()
            
            if self.cstate.AUDIOCHALLENGE:
                if self.verbose: print('captcha_audio.run(): audio challenge found')
                break
            else:
                if self.verbose: print('captcha_audio.run(): no audio challenge? repeat')
 
        if self.cstate.LIMIT_REACHED:
            if self.verbose: print('captcha_audio.run(): captcha try limit reached; try later')
            return False
        else:
            if self.verbose: print('captcha_audio.run(): no limit reached')
        
        for i in range(self.tries):
            if self.verbose: print(f'captcha_audio.run(): try {i}')
            audio_url = self.find_audio_url()
            text = retrieve_transcript(audio_url)
            if self.verbose: print('captcha_audio.run(): audio text: ',text)
            self.input_transcript(text)
            self.click_verify()
            
            self.cstate.update_state()
            
            if self.cstate.TICKED:
                if self.verbose: print(f'captcha_audio.run(): transcript correct')
                return True
            else:
                if self.verbose: print(f'captcha_audio.run(): transcript incorrect')
        
        if self.verbose: print('captcha_audio.run(): limit reached without a success')
        return False
    