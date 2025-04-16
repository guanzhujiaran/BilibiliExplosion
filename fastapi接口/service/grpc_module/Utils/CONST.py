ANDROID_VERSIONS = {
    '1.0': 1, '1.1': 2, '1.5': 3, '1.6': 4, '2.0': 5, '2.0.1': 6, '2.1': 7, '2.2': 8, '2.3': 9, '2.3.3': 10,
    '3.0': 11, '3.1': 12, '3.2': 13, '4.0': 14, '4.0.3': 15, '4.0.4': 15, '4.1': 16, '4.1.1': 16, '4.2': 17,
    '4.3': 18, '4.4': 19, '4.4W': 20, '5.0': 21, '5.1': 22, '6.0': 23, '6': 23, '7.0': 24, '7': 24, '7.1': 25,
    '8.0': 26, '8': 26, '8.0.0': 26,
    '8.1': 27, '9.0': 28, '9': 28, '10.0': 29, '10': 29, '11.0': 30, '11': 30, '12.0': 31, '12': 31, '12.1': 32,
    '13.0': 33,
    '13': 33
}
ANDROID_KERNELS = {
    '1.0': ["2.6.27"],
    '1.1': ["2.6.27"],
    '1.5': ["2.6.27"],
    '1.6': ["2.6.29"],
    '2.0': ["2.6.29"],
    '2': ["2.6.29"],
    '2.1': ["2.6.29"],
    '2.2': ["2.6.32"],
    '2.3': ["2.6.35"],
    '3.0': ["2.6.39", "3.0.8"],
    '3': ["2.6.39", "3.0.8"],
    '3.1': ["2.6.39", "3.0.8"],
    '3.2': ["2.6.39", "3.0.8"],
    '4.0': ["3.0.1", "3.0.31"],
    '4': ["3.0.1", "3.0.31"],
    '4.1': ["3.0.31", "3.4.67"],
    '4.2': ["3.4.0", "3.4.67"],
    '4.3': ["3.4.0", "3.4.113"],
    '4.4': ["3.4.0", "3.10.79"],
    '5.0': ["3.10.0", "3.18.31"],
    '5': ["3.10.0", "3.18.31"],
    '5.1': ["3.10.0", "3.18.31"],
    '6.0': ["3.10.0", "4.1.15"],
    '6': ["3.10.0", "4.1.15"],
    '7.0': ["3.10.0", "4.4.90", "4.9.0", "4.9.12"],
    '7': ["3.10.0", "4.4.90", "4.9.0", "4.9.12"],
    '7.1': ["3.10.0", "4.4.90", "4.9.0", "4.9.12"],
    '8.0': ["4.4.0", "4.14.11"],
    '8.0.0': ["4.4.0", "4.14.11"],
    '8': ["4.4.0", "4.14.11"],
    '8.1': ["4.4.0", "4.14.11"],
    '9.0': ["4.4.0", "4.9.125", "4.14.0", "4.19.52"],
    '9': ["4.4.0", "4.9.125", "4.14.0", "4.19.52"],
    '10.0': ["4.4.0", "4.14.113", "4.19.0", "5.1.17"],
    '10': ["4.4.0", "4.14.113", "4.19.0", "5.1.17"],
    '11.0': ["4.14.113", "4.19.107", "5.4.0", "5.4.43"],
    '11': ["4.14.113", "4.19.107", "5.4.0", "5.4.43"],
    '12.0': ["4.19.170", "5.10.42", "5.10.0", "5.15.10"],
    '12': ["4.19.170", "5.10.42", "5.10.0", "5.15.10"],
    '12.1': ["4.19.170", "5.10.42", "5.10.0", "5.15.10"],
    '13.0': ["5.10.0", "5.15.76", "5.10.0", "6.1.11"],
    '13': ["5.10.0", "5.15.76", "5.10.0", "6.1.11"]
}

MemSizes = {
    "63.75GB": 68386580480,  # 63.75 GB in bytes (63 * 1024 * 1024 * 1024 + 0.75 * 1024 * 1024 * 1024)
    "63GB": 67645799936,  # 63 GB in bytes (63 * 1024 * 1024 * 1024)
    "31.75GB": 34113178624,  # 31.75 GB in bytes (31 * 1024 * 1024 * 1024 + 0.75 * 1024 * 1024 * 1024)
    "31GB": 33276569548,  # 31 GB in bytes (31 * 1024 * 1024 * 1024)
    "15.75GB": 16888498688,  # 15.75 GB in bytes (15 * 1024 * 1024 * 1024 + 0.75 * 1024 * 1024 * 1024)
    "15GB": 16106127360,  # 15 GB in bytes (15 * 1024 * 1024 * 1024)
    "7.75GB": 8323072512,  # 7.75 GB in bytes (7 * 1024 * 1024 * 1024 + 0.75 * 1024 * 1024 * 1024)
    "7GB": 7516192768,  # 7 GB in bytes (7 * 1024 * 1024 * 1024)
    "3.75GB": 3932160000,  # 3.75 GB in bytes (3 * 1024 * 1024 * 1024 + 0.75 * 1024 * 1024 * 1024)
    "3.5GB": 3758096384,  # 3.5 GB in bytes (3.5 * 1024 * 1024 * 1024)
    "3.25GB": 3489660928,  # 3.25 GB in bytes (3 * 1024 * 1024 * 1024 + 0.25 * 1024 * 1024 * 1024)
    "3GB": 3221225472,  # 3 GB in bytes (3 * 1024 * 1024 * 1024)
    "2.75GB": 2949672960,  # 2.75 GB in bytes (2 * 1024 * 1024 * 1024 + 0.75 * 1024 * 1024 * 1024)
    "2.5GB": 2684354560,  # 2.5 GB in bytes (2.5 * 1024 * 1024 * 1024)
    "2.25GB": 2419235072,  # 2.25 GB in bytes (2 * 1024 * 1024 * 1024 + 0.25 * 1024 * 1024 * 1024)
    "2GB": 2147483648,  # 2 GB in bytes (2 * 1024 * 1024 * 1024)
    "1.75GB": 1879048192,  # 1.75 GB in bytes (1 * 1024 * 1024 * 1024 + 0.75 * 1024 * 1024 * 1024)
    "1.5GB": 1572864000,  # 1.5 GB in bytes (1.5 * 1024 * 1024 * 1024)
    "1.25GB": 1300234240,  # 1.25 GB in bytes (1 * 1024 * 1024 * 1024 + 0.25 * 1024 * 1024 * 1024)
}
CPUFreqs = {
    "3.0GHz": int(3_000_000_000 * (2865600 / 3_000_000_000)),  # 3.0 GHz in Hz
    "2.8GHz": int(2_800_000_000 * (2865600 / 2_800_000_000)),  # 2.8 GHz in Hz
    "2.5GHz": int(2_500_000_000 * (2865600 / 2_500_000_000)),  # 2.5 GHz in Hz
    "2.2GHz": int(2_200_000_000 * (2865600 / 2_200_000_000)),  # 2.2 GHz in Hz
    "2.0GHz": int(2_000_000_000 * (2865600 / 2_000_000_000)),  # 2.0 GHz in Hz
    "1.8GHz": int(1_800_000_000 * (2865600 / 1_800_000_000)),  # 1.8 GHz in Hz
    "1.5GHz": int(1_500_000_000 * (2865600 / 1_500_000_000))  # 1.5 GHz in Hz
}
ProductDevices = [
    "marlin",  # Google Pixel XL (2016)
    "sailfish",  # Google Pixel (2016)
    "taimen",  # Google Pixel 2 XL (2017)
    "walleye",  # Google Pixel 2 (2017)
    "blueline",  # Google Pixel 3 XL (2018)
    "crosshatch",  # Google Pixel 3 (2018)
    "coral",  # Google Pixel 4 (2019)
    "flame",  # Google Pixel 4a (2020)
    "sunfish",  # Google Pixel 4a (2020) - 仅限某些地区
    "redfin",  # Google Pixel 5 (2020)
    "bramble",  # Google Pixel 4a (5G) (2020)
    "barbet",  # Google Pixel 5a (2021)
    "oriole",  # Google Pixel 6 (2021)
    "raven",  # Google Pixel 6 Pro (2021)
    "bluejay",  # Google Pixel 6a (2022)
    "panther",  # Google Pixel 7 (2022)
    "cheetah",  # Google Pixel 7 Pro (2022)
    "lynx",  # Google Pixel 7a (2023)
    "falcon",  # Google Pixel 8 (2023)
    "halibut",  # Google Pixel 8 Pro (2023)
    "grouper",  # Google Pixel Tablet (2023)
    "angler",  # Huawei Nexus 6P
    "bullhead",  # LG Nexus 5X
    "shamu",  # Motorola Nexus 6
    "hammerhead",  # LG Nexus 5
    "mako",  # LG Nexus 4
    "flo",  # Asus Nexus 7 (2013, Wi-Fi)
    "deb",  # Asus Nexus 7 (2013, Mobile)
    "nakasi",  # Asus Nexus 7 (2012)
    "tilapia",  # Asus Nexus 7 (2012, Wi-Fi)
    "grouper",  # Asus Nexus 7 (2012, Mobile)
    "tuna",  # Samsung Galaxy Nexus
    "toro",  # Samsung Galaxy Nexus (Sprint)
    "toroplus",  # Samsung Galaxy Nexus (Verizon)
    "maguro",  # Samsung Galaxy Nexus (International)
    "manta",  # Sony Xperia Z Ultra Google Play Edition
    "occam",  # LG Optimus G Pro Google Play Edition
    "hammerhead",  # LG Nexus 5
    "mako",  # LG Nexus 4
    "manta",  # Sony Xperia Z Ultra Google Play Edition
    "flo",  # Asus Nexus 7 (2013, Wi-Fi)
    "deb",  # Asus Nexus 7 (2013, Mobile)
    "nakasi",  # Asus Nexus 7 (2012)
    "tilapia",  # Asus Nexus 7 (2012, Wi-Fi)
    "grouper",  # Asus Nexus 7 (2012, Mobile)
    "tuna",  # Samsung Galaxy Nexus
    "toro",  # Samsung Galaxy Nexus (Sprint)
    "toroplus",  # Samsung Galaxy Nexus (Verizon)
    "maguro",  # Samsung Galaxy Nexus (International)
]

Languages = [
    "zh",  # 中文 (Chinese)
    "en",  # 英语 (English)
    "es",  # 西班牙语 (Spanish)
    "fr",  # 法语 (French)
    "de",  # 德语 (German)
    "it",  # 意大利语 (Italian)
    "ja",  # 日语 (Japanese)
    "ko",  # 韩语 (Korean)
    "pt",  # 葡萄牙语 (Portuguese)
    "ru",  # 俄语 (Russian)
    "ar",  # 阿拉伯语 (Arabic)
    "nl",  # 荷兰语 (Dutch)
    "pl",  # 波兰语 (Polish)
    "tr",  # 土耳其语 (Turkish)
    "th",  # 泰语 (Thai)
    "vi",  # 越南语 (Vietnamese)
    "hi",  # 印地语 (Hindi)
    "id",  # 印度尼西亚语 (Indonesian)
    "ms",  # 马来语 (Malay)
    "sv",  # 瑞典语 (Swedish)
    "da",  # 丹麦语 (Danish)
    "no",  # 挪威语 (Norwegian)
    "fi",  # 芬兰语 (Finnish)
    "cs",  # 捷克语 (Czech)
    "hu",  # 匈牙利语 (Hungarian)
    "ro",  # 罗马尼亚语 (Romanian)
    "el",  # 希腊语 (Greek)
]
Countries = [
    "AF",  # 阿富汗 (Afghanistan)
    "AX",  # 奥兰群岛 (Åland Islands)
    "AL",  # 阿尔巴尼亚 (Albania)
    "DZ",  # 阿尔及利亚 (Algeria)
    "AS",  # 美属萨摩亚 (American Samoa)
    "AD",  # 安道尔 (Andorra)
    "AO",  # 安哥拉 (Angola)
    "AI",  # 安圭拉 (Anguilla)
    "AQ",  # 南极洲 (Antarctica)
    "AG",  # 安提瓜和巴布达 (Antigua and Barbuda)
    "AR",  # 阿根廷 (Argentina)
    "AM",  # 亚美尼亚 (Armenia)
    "AW",  # 阿鲁巴 (Aruba)
    "AU",  # 澳大利亚 (Australia)
    "AT",  # 奥地利 (Austria)
    "AZ",  # 阿塞拜疆 (Azerbaijan)
    "BS",  # 巴哈马 (Bahamas)
    "BH",  # 巴林 (Bahrain)
    "BD",  # 孟加拉国 (Bangladesh)
    "BB",  # 巴巴多斯 (Barbados)
    "BY",  # 白俄罗斯 (Belarus)
    "BE",  # 比利时 (Belgium)
    "BZ",  # 伯利兹 (Belize)
    "BJ",  # 贝宁 (Benin)
    "BM",  # 百慕大 (Bermuda)
    "BT",  # 不丹 (Bhutan)
    "BO",  # 玻利维亚 (Bolivia, Plurinational State of)
    "BQ",  # 博内尔、圣尤斯特歇斯和萨巴 (Bonaire, Sint Eustatius and Saba)
    "BA",  # 波斯尼亚和黑塞哥维那 (Bosnia and Herzegovina)
    "BW",  # 博茨瓦纳 (Botswana)
    "BV",  # 布韦岛 (Bouvet Island)
    "BR",  # 巴西 (Brazil)
    "IO",  # 英属印度洋领地 (British Indian Ocean Territory)
    "BN",  # 文莱 (Brunei Darussalam)
    "BG",  # 保加利亚 (Bulgaria)
    "BF",  # 布基纳法索 (Burkina Faso)
    "BI",  # 布隆迪 (Burundi)
    "KH",  # 柬埔寨 (Cambodia)
    "CM",  # 喀麦隆 (Cameroon)
    "CA",  # 加拿大 (Canada)
    "CV",  # 佛得角 (Cape Verde)
    "KY",  # 开曼群岛 (Cayman Islands)
    "CF",  # 中非共和国 (Central African Republic)
    "TD",  # 恰德 (Chad)
    "CL",  # 智利 (Chile)
    "CN",  # 中国 (China)
    "CX",  # 圣诞岛 (Christmas Island)
    "CC",  # 科科斯（基灵）群岛 (Cocos (Keeling) Islands)
    "CO",  # 哥伦比亚 (Colombia)
    "KM",  # 科摩罗 (Comoros)
    "CG",  # 刚果 (Congo)
    "CD",  # 刚果民主共和国 (Congo, The Democratic Republic of the)
    "CK",  # 库克群岛 (Cook Islands)
    "CR",  # 哥斯达黎加 (Costa Rica)
    "CI",  # 科特迪瓦 (Côte d'Ivoire)
    "HR",  # 克罗地亚 (Croatia)
    "CU",  # 古巴 (Cuba)
    "CW",  # 库拉索 (Curaçao)
    "CY",  # 塞浦路斯 (Cyprus)
    "CZ",  # 捷克 (Czech Republic)
    "DK",  # 丹麦 (Denmark)
    "DJ",  # 吉布提 (Djibouti)
    "DM",  # 多米尼克 (Dominica)
    "DO",  # 多米尼加共和国 (Dominican Republic)
    "EC",  # 厄瓜多尔 (Ecuador)
    "EG",  # 埃及 (Egypt)
    "SV",  # 萨尔瓦多 (El Salvador)
    "GQ",  # 赤道几内亚 (Equatorial Guinea)
    "ER",  # 厄立特里亚 (Eritrea)
    "EE",  # 爱沙尼亚 (Estonia)
    "ET",  # 埃塞俄比亚 (Ethiopia)
    "FK",  # 福克兰群岛（马尔维纳斯） (Falkland Islands (Malvinas))
    "FO",  # 法罗群岛 (Faroe Islands)
    "FJ",  # 斐济 (Fiji)
    "FI",  # 芬兰 (Finland)
    "FR",  # 法国 (France)
    "GF",  # 法属圭亚那 (French Guiana)
    "PF",  # 法属波利尼西亚 (French Polynesia)
    "TF",  # 法属南部领地 (French Southern Territories)
    "GA",  # 加蓬 (Gabon)
    "GM",  # 冈比亚 (Gambia)
    "GE",  # 格鲁吉亚 (Georgia)
    "DE",  # 德国 (Germany)
    "GH",  # 加纳 (Ghana)
    "GI",  # 直布罗陀 (Gibraltar)
    "GR",  # 希腊 (Greece)
    "GL",  # 格陵兰 (Greenland)
    "GD",  # 格林纳达 (Grenada)
    "GP",  # 瓜德罗普 (Guadeloupe)
    "GU",  # 关岛 (Guam)
    "GT",  # 危地马拉 (Guatemala)
    "GG",  # 根西岛 (Guernsey)
    "GN",  # 几内亚 (Guinea)
    "GW",  # 几内亚比绍 (Guinea-Bissau)
    "GY",  # 圭亚那 (Guyana)
    "HT",  # 海地 (Haiti)
    "HM",  # 赫德岛和麦克唐纳群岛 (Heard Island and McDonald Islands)
    "VA",  # 梵蒂冈 (Holy See (Vatican City State))
    "HN",  # 洪都拉斯 (Honduras)
    "HK",  # 中国香港特别行政区 (Hong Kong)
    "HU",  # 匈牙利 (Hungary)
    "IS",  # 冰岛 (Iceland)
    "IN",  # 印度 (India)
    "ID",  # 印度尼西亚 (Indonesia)
    "IR",  # 伊朗 (Iran, Islamic Republic of)
    "IQ",  # 伊拉克 (Iraq)
    "IE",  # 爱尔兰 (Ireland)
    "IM",  # 马恩岛 (Isle of Man)
    "IL",  # 以色列 (Israel)
    "IT",  # 意大利 (Italy)
    "JM",  # 牙买加 (Jamaica)
    "JP",  # 日本 (Japan)
    "JE",  # 泽西岛 (Jersey)
    "JO",  # 约旦 (Jordan)
    "KZ",  # 哈萨克斯坦 (Kazakhstan)
    "KE",  # 肯尼亚 (Kenya)
    "KI",  # 基里巴斯 (Kiribati)
    "KP",  # 朝鲜 (Korea, Democratic People's Republic of)
    "KR",  # 韩国 (Korea, Republic of)
    "KW",  # 科威特 (Kuwait)
    "KG",  # 吉尔吉斯斯坦 (Kyrgyzstan)
    "LA",  # 老挝 (Lao People's Democratic Republic)
    "LV",  # 拉脱维亚 (Latvia)
    "LB",  # 黎巴嫩 (Lebanon)
    "LS",  # 莱索托 (Lesotho)
    "LR",  # 利比里亚 (Liberia)
    "LY",  # 利比亚 (Libya)
    "LI",  # 列支敦士登 (Liechtenstein)
    "LT",  # 立陶宛 (Lithuania)
    "LU",  # 卢森堡 (Luxembourg)
    "MO",  # 中国澳门特别行政区 (Macao)
    "MK",  # 马其顿 (Macedonia, the former Yugoslav Republic of)
    "MG",  # 马达加斯加 (Madagascar)
    "MW",  # 马拉维 (Malawi)
    "MY",  # 马来西亚 (Malaysia)
    "MV",  # 马尔代夫 (Maldives)
    "ML",  # 马里 (Mali)
    "MT",  # 马耳他 (Malta)
    "MH",  # 马绍尔群岛 (Marshall Islands)
    "MQ",  # 马提尼克 (Martinique)
    "MR",  # 毛里塔尼亚 (Mauritania)
    "MU",  # 毛里求斯 (Mauritius)
    "YT",  # 马约特 (Mayotte)
    "MX",  # 墨西哥 (Mexico)
    "FM",  # 密克罗尼西亚联邦 (Micronesia, Federated States of)
    "MD",  # 摩尔多瓦 (Moldova, Republic of)
    "MC",  # 摩纳哥 (Monaco)
    "MN",  # 蒙古 (Mongolia)
    "ME",  # 黑山 (Montenegro)
    "MS",  # 蒙特塞拉特 (Montserrat)
    "MA",  # 摩洛哥 (Morocco)
    "MZ",  # 莫桑比克 (Mozambique)
    "MM",  # 缅甸 (Myanmar)
    "NA",  # 纳米比亚 (Namibia)
    "NR",  # 瑙鲁 (Nauru)
    "NP",  # 尼泊尔 (Nepal)
    "NL",  # 荷兰 (Netherlands)
    "NC",  # 新喀里多尼亚 (New Caledonia)
    "NZ",  # 新西兰 (New Zealand)
    "NI",  # 尼加拉瓜 (Nicaragua)
    "NE",  # 尼日尔 (Niger)
    "NG",  # 尼日利亚 (Nigeria)
    "NU",  # 尼乌埃 (Niue)
    "NF",  # 诺福克岛 (Norfolk Island)
    "MP",  # 北马里亚纳群岛 (Northern Mariana Islands)
    "NO",  # 挪威 (Norway)
    "OM",  # 阿曼 (Oman)
    "PK",  # 巴基斯坦 (Pakistan)
    "PW",  # 帕劳 (Palau)
    "PS",  # 巴勒斯坦 (Palestine, State of)
    "PA",  # 巴拿马 (Panama)
    "PG",  # 巴布亚新几内亚 (Papua New Guinea)
    "PY",  # 巴拉圭 (Paraguay)
    "PE",  # 秘鲁 (Peru)
    "PH",  # 菲律宾 (Philippines)
    "PN",  # 皮特凯恩 (Pitcairn)
    "PL",  # 波兰 (Poland)
    "PT",  # 葡萄牙 (Portugal)
    "PR",  # 波多黎各 (Puerto Rico)
    "QA",  # 卡塔尔 (Qatar)
    "RE",  # 留尼汪 (Réunion)
    "RO",  # 罗马尼亚 (Romania)
    "RU",  # 俄罗斯 (Russian Federation)
    "RW",  # 卢旺达 (Rwanda)
    "BL",  # 圣巴泰勒米 (Saint Barthélemy)
    "SH",  # 圣赫勒拿、阿森松和特里斯坦达库尼亚 (Saint Helena, Ascension and Tristan da Cunha)
    "KN",  # 圣基茨和尼维斯 (Saint Kitts and Nevis)
    "LC",  # 圣卢西亚 (Saint Lucia)
    "MF",  # 圣马丁（法国部分） (Saint Martin (French part))
    "PM",  # 圣皮埃尔和密克隆 (Saint Pierre and Miquelon)
    "VC",  # 圣文森特和格林纳丁斯 (Saint Vincent and the Grenadines)
    "WS",  # 萨摩亚 (Samoa)
    "SM",  # 圣马力诺 (San Marino)
    "ST",  # 圣多美和普林西比 (Sao Tome and Principe)
    "SA",  # 沙特阿拉伯 (Saudi Arabia)
    "SN",  # 塞内加尔 (Senegal)
    "RS",  # 塞尔维亚 (Serbia)
    "SC",  # 塞舌尔 (Seychelles)
    "SL",  # 塞拉利昂 (Sierra Leone)
    "SG",  # 新加坡 (Singapore)
    "SX",  # 荷属圣马丁 (Sint Maarten (Dutch part))
    "SK",  # 斯洛伐克 (Slovakia)
    "SI",  # 斯洛文尼亚 (Slovenia)
    "SB",  # 所罗门群岛 (Solomon Islands)
    "SO",  # 索马里 (Somalia)
    "ZA",  # 南非 (South Africa)
    "GS",  # 南乔治亚和南桑威奇群岛 (South Georgia and the South Sandwich Islands)
    "SS",  # 南苏丹 (South Sudan)
    "ES",  # 西班牙 (Spain)
    "LK",  # 斯里兰卡 (Sri Lanka)
    "SD",  # 苏丹 (Sudan)
    "SR",  # 苏里南 (Suriname)
    "SJ",  # 斯瓦尔巴和扬马延 (Svalbard and Jan Mayen)
    "SZ",  # 斯威士兰 (Swaziland)
    "SE",  # 瑞典 (Sweden)
    "CH",  # 瑞士 (Switzerland)
    "SY",  # 叙利亚 (Syrian Arab Republic)
    "TW",  # 中国台湾省 (Taiwan, Province of China)
    "TJ",  # 塔吉克斯坦 (Tajikistan)
    "TZ",  # 坦桑尼亚 (Tanzania, United Republic of)
    "TH",  # 泰国 (Thailand)
    "TL",  # 东帝汶 (Timor-Leste)
    "TG",  # 多哥 (Togo)
    "TK",  # 托克劳 (Tokelau)
    "TO",  # 汤加 (Tonga)
    "TT",  # 特立尼达和多巴哥 (Trinidad and Tobago)
    "TN",  # 突尼斯 (Tunisia)
    "TR",  # 土耳其 (Turkey)
    "TM",  # 土库曼斯坦 (Turkmenistan)
    "TC",  # 特克斯和凯科斯群岛 (Turks and Caicos Islands)
    "TV",  # 图瓦卢 (Tuvalu)
    "UG",  # 乌干达 (Uganda)
    "UA",  # 乌克兰 (Ukraine)
    "AE",  # 阿联酋 (United Arab Emirates)
    "GB",  # 英国 (United Kingdom)
    "US",  # 美国 (United States)
    "UM",  # 美国本土外小岛屿 (United States Minor Outlying Islands)
    "UY",  # 乌拉圭 (Uruguay)
    "UZ",  # 乌兹别克斯坦 (Uzbekistan)
    "VU",  # 瓦努阿图 (Vanuatu)
    "VE",  # 委内瑞拉 (Venezuela, Bolivarian Republic of)
    "VN",  # 越南 (Viet Nam)
    "VG",  # 英属维尔京群岛 (Virgin Islands, British)
    "VI",  # 美属维尔京群岛 (Virgin Islands, U.S.)
    "WF",  # 瓦利斯和富图纳 (Wallis and Futuna)
    "EH",  # 西撒哈拉 (Western Sahara)
    "YE",  # 也门 (Yemen)
    "ZM",  # 赞比亚 (Zambia)
    "ZW"  # 津巴布韦 (Zimbabwe)
]
NetworkTypes = [
    "GPRS",  # 通用分组无线服务 (General Packet Radio Service)
    "EDGE",  # 增强数据速率 GSM 演进 (Enhanced Data rates for GSM Evolution)
    "UMTS",  # 通用移动通信系统 (Universal Mobile Telecommunications System)
    "HSDPA",  # 高速下行分组接入 (High-Speed Downlink Packet Access)
    "HSUPA",  # 高速上行分组接入 (High-Speed Uplink Packet Access)
    "HSPA",  # 高速分组接入 (High-Speed Packet Access)
    "HSPA+",  # 增强型高速分组接入 (Evolved High-Speed Packet Access)
    "CDMA",  # 码分多址 (Code Division Multiple Access)
    "EVDO_0",  # EV-DO 版本 0 (Evolution-Data Optimized version 0)
    "EVDO_A",  # EV-DO 版本 A (Evolution-Data Optimized version A)
    "1xRTT",  # 单载波无线电传输技术 (Single-Carrier Radio Transmission Technology)
    "EHRPD",  # 增强型高速分组数据 (Enhanced High Rate Packet Data)
    "LTE",  # 长期演进 (Long-Term Evolution)
    "TD_SCDMA",  # 时分同步码分多址 (Time Division Synchronous Code Division Multiple Access)
    "IWLAN",  # 集成无线局域网 (Integrated Wireless Local Area Network)
    "NR",  # 新无线 (New Radio, 5G)
]
UsbStates = [
    # "adb",        # ADB 模式，允许通过 USB 进行调试
    # "mtp",        # MTP（媒体传输协议）模式，允许文件传输
    # "ptp",        # PTP/（图片传输协议）模式，通常用于照片传输
    # "midi",       # MIDI（音乐设备数字接口）模式
    "audio_source",  # 音频源模式
    # "audio_sink",    # 音频接收器模式
    # "accessory",     # 配件模式，允许与特定配件通信
    # "diag",         # 诊断模式，用于硬件诊断
    "charging",  # 仅充电模式，不进行数据传输
]

CPUAbiLists = [
    "arm64-v8a,armeabi-v7a,armeabi",  # 大多数现代 ARM 设备
]
CPUHardwares = [
    "Qualcomm Technologies, Inc SM8550",  # Snapdragon 8 Gen 2 (截至2024年)
    "Qualcomm Technologies, Inc SM8450",  # Snapdragon 8 Gen 1
    "Qualcomm Technologies, Inc SM8350",  # Snapdragon 888
    "Qualcomm Technologies, Inc SM8250",  # Snapdragon 865
    "Qualcomm Technologies, Inc SDM855",  # Snapdragon 855
    "Qualcomm Technologies, Inc SDM845",  # Snapdragon 845
    "Qualcomm Technologies, Inc SDM835",  # Snapdragon 835
    "Qualcomm Technologies, Inc SDM821",  # Snapdragon 821
    "Qualcomm Technologies, Inc SDM820",  # Snapdragon 820
    "Qualcomm Technologies, Inc MSM8996",  # Snapdragon 820
    "Qualcomm Technologies, Inc MSM8994",  # Snapdragon 810
    "Qualcomm Technologies, Inc MSM8974",  # Snapdragon 800
    "Qualcomm Technologies, Inc MSM8998",  # Snapdragon 835
    "Qualcomm Technologies, Inc SDM660",  # Snapdragon 660
    "Qualcomm Technologies, Inc SDM670",  # Snapdragon 670
    "Qualcomm Technologies, Inc SDM675",  # Snapdragon 675
    "Qualcomm Technologies, Inc SDM678",  # Snapdragon 678
    "Qualcomm Technologies, Inc SDM636",  # Snapdragon 636
    "Qualcomm Technologies, Inc SDM632",  # Snapdragon 632
    "Qualcomm Technologies, Inc SDM626",  # Snapdragon 626
    "Qualcomm Technologies, Inc SDM625",  # Snapdragon 625
    "Qualcomm Technologies, Inc SDM617",  # Snapdragon 617
    "Qualcomm Technologies, Inc MSM8953",  # Snapdragon 625
    "Qualcomm Technologies, Inc MSM8937",  # Snapdragon 430/427
    "Qualcomm Technologies, Inc MSM8952",  # Snapdragon 617/616/615
    "Qualcomm Technologies, Inc MSM8939",  # Snapdragon 615
    "Qualcomm Technologies, Inc MSM8916",  # Snapdragon 410
    "Qualcomm Technologies, Inc MSM8226",  # Snapdragon 400
    "Qualcomm Technologies, Inc MSM8610",  # Snapdragon 400
]

BatteryStates = [
    'BATTERY_STATUS_CHARGING',
    'BATTERY_STATUS_DISCHARGING',
    'BATTERY_STATUS_NOT_CHARGING',
    'BATTERY_STATUS_FULL',
]

ScreenDPIs = [
    '1080,2400,405',  # Samsung Galaxy S21 - FHD+ (1080x2400), 421 PPI
    '1440,3200,515',  # Samsung Galaxy S21 Ultra - WQHD+ (1440x3200), 515 PPI
    '1080,2400,409',  # Google Pixel 6 - FHD+ (1080x2400), 411 PPI
    '1440,3120,512',  # Google Pixel 6 Pro - QHD+ (1440x3120), 512 PPI
    '1080,2400,405',  # OnePlus 9 - FHD+ (1080x2400), 402 PPI
    '1440,3200,525',  # OnePlus 9 Pro - QHD+ (1440x3200), 525 PPI
    '1080,2400,405',  # Xiaomi Mi 11 - FHD+ (1080x2400), 395 PPI
    '1440,3200,515',  # Xiaomi Mi 11 Ultra - QHD+ (1440x3200), 515 PPI
    '1080,2400,405',  # Oppo Find X3 Pro - FHD+ (1080x2400), 450 PPI
    '1440,3200,525',  # Oppo Find X3 Pro - QHD+ (1440x3200), 525 PPI
    '1080,2400,405',  # Vivo X70 Pro+ - FHD+ (1080x2400), 398 PPI
    '1440,3200,517',  # Vivo X70 Pro+ - QHD+ (1440x3200), 517 PPI
    '1080,2400,405',  # Realme GT 2 Pro - FHD+ (1080x2400), 394 PPI
    '1440,3200,525',  # Realme GT 2 Pro - QHD+ (1440x3200), 525 PPI
    '1080,2400,405',  # Huawei P50 Pro - FHD+ (1080x2400), 439 PPI
    '1080,2400,405',  # Sony Xperia 1 III - 4K HDR OLED (1644x3840), 643 PPI
    '1080,2400,405',  # Motorola Edge 20 Pro - FHD+ (1080x2400), 395 PPI
    '1080,2400,405',  # LG Velvet - FHD+ (1080x2400), 395 PPI
]
