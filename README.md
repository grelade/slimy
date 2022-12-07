# What is slimy

You shall pass Google reCAPTCHA v2.

# Basic usage

Check out the [**notebook demo**](demo.ipynb).

You need selenium to run a programmable browser. Then, passing reCAPTCHA is simple:

    from slimy import captcha
    from selenium import webdriver

    driver = webdriver.Chrome()
    url = 'https://www.google.com/recaptcha/api2/demo'
    driver.get(url)
    is_successful = captcha(driver).pass_captcha()

# How does it work?

Instead of handling the image challenge, `slimy` takes on the audio challenge with the help of a `wav2vec` ML model.

# Limitations

Slimy uses a freely available `wav2vec` model provided by [Huggingface](http://huggingface.co). As such, it is not suitable for heavy-duty tasks. Still, in `config.py` you can provide your own API credentials and run your own model with paid plans.
