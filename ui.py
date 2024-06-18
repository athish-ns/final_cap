import os
import time
import subprocess
from PIL import Image
from twocaptcha import TwoCaptcha
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from seleniumbase import SB
import tkinter as tk
from tkinter import ttk, messagebox

def fill_in_search_criteria(driver, rd_number, date_of_crash):
    rd_number_field = driver.find_element(By.ID, "rd")
    date_of_crash_field = driver.find_element(By.ID, "crashDate")
    rd_number_field.send_keys(rd_number)
    date_of_crash_field.send_keys(date_of_crash)

def solve_recaptcha_twocaptcha(api_key, site_key, url):
    solver = TwoCaptcha(api_key)
    try:
        result = solver.recaptcha(sitekey=site_key, url=url)
        return result['code']
    except Exception as e:
        print(f"Error solving reCAPTCHA: {e}")
        raise

def take_full_page_screenshot(sb, file_name, folder):
    selector = "body"
    element = sb.wait_for_element_visible(selector)
    sb.driver.execute_script("document.body.style.zoom='60%'")
    time.sleep(2)  # Give some time for the zoom effect to apply
    height = element.size["height"]
    sb.set_window_size(1920, height)
    sb.save_element_as_image_file(selector, file_name, folder)

def lookup_crash_info(rd_prefix, rd_number_start, rd_number_end, date_of_crash, api_key_twocaptcha, recaptcha_site_key):
    for rd_number in range(rd_number_start, rd_number_end + 1):
        rd_number_str = f"{rd_prefix}{rd_number}"

        with SB(uc=True) as sb:
            url = "https://crash.chicagopolice.org/DriverInformationExchange/home"
            sb.driver.uc_open_with_reconnect(url, 6)

            try:
                WebDriverWait(sb.driver, 60).until(
                    EC.presence_of_element_located((By.ID, "rd"))
                )

                fill_in_search_criteria(sb.driver, rd_number_str, date_of_crash)

                captcha_response = solve_recaptcha_twocaptcha(api_key_twocaptcha, recaptcha_site_key, sb.driver.current_url)

                sb.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{captcha_response}";')

                time.sleep(5)

                sb.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

                # Debugging: Take a full-page screenshot after form submission
                screenshot_folder = os.path.dirname(os.path.abspath(__file__))
                screenshot_filename = f"debug_{rd_number_str}_{date_of_crash}.png"
                take_full_page_screenshot(sb, screenshot_filename, screenshot_folder)
                screenshot_path = os.path.join(screenshot_folder, screenshot_filename)
                print(f"Screenshot saved: {screenshot_path}")

                # Convert the screenshot to PDF
                pdf_path = os.path.join(screenshot_folder, f'{rd_number_str}_{date_of_crash}.pdf')
                try:
                    image = Image.open(screenshot_path)
                    image = image.convert('RGB')
                    image.save(pdf_path)
                    print(f"Screenshot converted to PDF: {pdf_path}")

                    subprocess.run(["start", "", pdf_path], shell=True)
                except Exception as pdf_conversion_error:
                    print(f"Error converting screenshot to PDF for RD {rd_number_str}: {pdf_conversion_error}")

                # Delay for 30 seconds after generating each report
                print(f"Waiting for 30 seconds before processing the next RD number...")
                time.sleep(30)

            except TimeoutException:
                print(f"Timed out waiting for elements to load for RD {rd_number_str}.")
            except NoSuchElementException as e:
                print(f"Element not found for RD {rd_number_str}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred for RD {rd_number_str}: {e}")

def start_lookup():
    rd_prefix = rd_prefix_entry.get()
    rd_number_start = int(rd_number_start_entry.get())
    rd_number_end = int(rd_number_end_entry.get())
    date_of_crash = date_of_crash_entry.get()
    api_key_twocaptcha = api_key_twocaptcha_entry.get()
    recaptcha_site_key = "6LfMvwkTAAAAAPCkEtxBHgi9l8CM2O2j8hiNojTr"  

    try:
        lookup_crash_info(rd_prefix, rd_number_start, rd_number_end, date_of_crash, api_key_twocaptcha, recaptcha_site_key)
        messagebox.showinfo("Success", "Lookup completed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Set up the GUI
root = tk.Tk()
root.title("Crash Info Lookup")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="RD Number Prefix").grid(row=0, column=0, sticky=tk.W)
rd_prefix_entry = ttk.Entry(frame)
rd_prefix_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))

ttk.Label(frame, text="RD Number Start").grid(row=1, column=0, sticky=tk.W)
rd_number_start_entry = ttk.Entry(frame)
rd_number_start_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))

ttk.Label(frame, text="RD Number End").grid(row=2, column=0, sticky=tk.W)
rd_number_end_entry = ttk.Entry(frame)
rd_number_end_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))

ttk.Label(frame, text="Date of Crash").grid(row=3, column=0, sticky=tk.W)
date_of_crash_entry = ttk.Entry(frame)
date_of_crash_entry.grid(row=3, column=1, sticky=(tk.W, tk.E))

ttk.Label(frame, text="2Captcha API Key").grid(row=4, column=0, sticky=tk.W)
api_key_twocaptcha_entry = ttk.Entry(frame)
api_key_twocaptcha_entry.grid(row=4, column=1, sticky=(tk.W, tk.E))

ttk.Button(frame, text="Start Lookup", command=start_lookup).grid(row=5, column=0, columnspan=2)

# Make the GUI responsive
for child in frame.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

root.mainloop()
