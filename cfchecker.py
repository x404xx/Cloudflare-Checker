import asyncio
import json
import os
from random import uniform
from sys import argv
from time import time

import httpx


class Colors:
    GREEN = '\033[38;5;121m'
    BGREEN = '\033[38;5;82m'
    WHITE = '\033[38;5;231m'
    LBLUE = '\033[38;5;117m'
    LPURPLE = '\033[38;5;141m'
    BYELLOW = '\033[38;5;226m'
    RED = '\033[38;5;196m'
    END = '\033[0m'


class CloudflareChecker:
    CONFIG_FILE = 'results.json'

    @staticmethod
    def get_query():
        return input(f'{Colors.GREEN}Enter a URL{Colors.END}: ')

    @staticmethod
    def clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def stop_info():
        print(f'Press "{Colors.LPURPLE}ENTER{Colors.END}" to stop the program!\n')

    @staticmethod
    def save_info(config_file: str):
        print(f'\n{Colors.BYELLOW}Output saved successfully as{Colors.END} "{Colors.LPURPLE}{config_file}{Colors.END}"\n')

    @staticmethod
    def error_info(url: str, error: httpx.HTTPError):
        print(f'{Colors.WHITE}Error{Colors.END}: {Colors.LBLUE}{url}{Colors.END} | {Colors.RED}{error}{Colors.END}\n')

    @staticmethod
    def now_checking(url: str):
        print(f'Now checking {Colors.LBLUE}{url}{Colors.END}')

    @staticmethod
    def load_urls(file_path: str):
        with open(file_path, 'r', encoding='utf8') as file:
            urls = [line.strip() for line in file if line.strip()]
        return urls

    @classmethod
    def save_results(cls, results: dict):
        with open(cls.CONFIG_FILE, 'w', encoding='utf8') as file:
            json.dump(results, file, indent=4)
        cls.save_info(cls.CONFIG_FILE)

    @staticmethod
    def time_taken(started_time):
        elapsed = round((time() - started_time), 2)
        return (
            f'{Colors.BGREEN}{round(elapsed * 1000)}{Colors.END} miliseconds!'
            if elapsed < 1
            else f'{Colors.BGREEN}{elapsed}{Colors.END} seconds!'
            if elapsed < 60
            else f'{Colors.BGREEN}{int(elapsed // 60)}{Colors.END} minutes {Colors.BGREEN}{int(elapsed % 60)}{Colors.END} seconds!'
        )

    @staticmethod
    async def check_cloudflare(response: httpx.Response):
        headers = [header.lower() for header in response.headers]
        return {
            'code': response.status_code,
            'cloudflare': 'server' in headers and response.headers['server'] == 'cloudflare',
            'challenge': 'cf-mitigated' in headers,
            'chl-bypass': 'cf-chl-bypass' in headers,
            'cf-ray': 'cf-ray' in headers,
            'cf-cache': 'cf-cache-status' in headers,
        }

    @classmethod
    async def process_url(cls, client: httpx.AsyncClient, url: str, mass=False):
        if mass:
            cls.now_checking(url)
        try:
            response = await client.head(url)
            return await cls.check_cloudflare(response)
        except httpx.HTTPError as error:
            return {'error': str(error)}

    @classmethod
    async def mass_check(cls, client: httpx.AsyncClient, file_path: str):
        urls = cls.load_urls(file_path)
        tasks = [cls.process_url(client, url, True) for url in urls]
        completed_tasks = await asyncio.gather(*tasks)
        results = {url: result for url, result in zip(urls, completed_tasks)}
        cls.save_results(results)

    @classmethod
    async def single_check(cls, client: httpx.AsyncClient):
        cls.clear_console()
        cls.stop_info()
        while True:
            url = cls.get_query()
            if not url:
                print('\nBye..\n')
                break
            print()
            results = await cls.process_url(client, url)
            if 'error' in results:
                error = results.get('error')
                cls.error_info(url, error)
                continue
            else:
                print(json.dumps({url: results}, indent=4))
                print()

    @classmethod
    async def start_program(cls):
        async with httpx.AsyncClient(timeout=uniform(10, 15)) as client:
            if len(argv) == 2:
                started_mass = time()
                await cls.mass_check(client, argv[-1])
                print(f'Time taken: {cls.time_taken(started_mass)}\n')
            else:
                await cls.single_check(client)


if __name__ == '__main__':
    asyncio.run(CloudflareChecker.start_program())
