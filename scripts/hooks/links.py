import logging

from dataclasses import dataclass
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.nav import Link


class CustomLink(Link):
    def __init__(self, **kwargs):
        self.meta = kwargs.pop('meta', {})
        super().__init__(**kwargs)

@dataclass
class LinkData:
    name: str
    url: str
    description: str
    button_icon: str
    link_icon: str

LINKS = [
    LinkData(
        name="Author's Wiki",
        url='https://wiki.virtualguard101.com',
        description='',  # 添加描述
        button_icon='fontawesome/solid/house',
        link_icon='fontawesome/solid/house',
    ),
]

log = logging.getLogger('mkdocs.plugins')

def on_config(config: MkDocsConfig):
    ''' 底部按钮 '''
    buttons = config.extra.setdefault('social', [])
    buttons.extend(map(lambda l: {
        'name': l.name,
        'icon': l.button_icon,
        'link': l.url,
    }, LINKS))
    return config

def on_nav(nav: Navigation, config: MkDocsConfig, files: Files):
    ''' 导航栏链接 '''
    for l in LINKS:
        link = CustomLink(title=l.name, url=l.url, meta = {'icon': l.link_icon})
        nav.items.append(link)

    # # 在index后插入链接（索引1位置）
    # for i, link_data in enumerate(LINKS):

    #     # 创建带描述的链接 - 使用HTML格式
    #     link_html = f'<span class="nav-link-title">{link_data.name}</span><span class="nav-link-description">{link_data.description}</span>'
    #     link = Link(title=link_html, url=link_data.url)

    #     link = Link(title=link_data.name, url=link_data.url)
    #     link.meta = { 'icon': link_data.link_icon }
    #     # 计算插入位置（1 + i 确保顺序正确）
    #     insert_position = 1 + i
    #     # 防止索引越界
    #     if insert_position > len(nav.items):
    #         nav.items.append(link)
    #     else:
    #         nav.items.insert(insert_position, link)
    return nav
