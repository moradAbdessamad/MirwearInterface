from groq import Groq
import os
import json
import datetime
import re

# Initialize the Groq client with your API key
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# User wardrobe data
wardrobe_data = {
        "1163.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "dodgerblue",
        "season": "Summer",
        "style": "Casual"
    },
    "12285.jpg": {
        "type": "Leggings",
        "gender": "Women",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Ethnic"
    },
    "12286.jpg": {
        "type": "Trousers",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Formal"
    },
    "12287.jpg": {
        "type": "Leggings",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "12288.jpg": {
        "type": "Trousers",
        "gender": "Women",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "12289.jpg": {
        "type": "Trousers",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "12290.jpg": {
        "type": "Leggings",
        "gender": "Women",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Ethnic"
    },
    "12348.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "lightblue",
        "season": "Summer",
        "style": "Formal"
    },
    "12350.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "black",
        "season": "Fall",
        "style": "Casual"
    },
    "12354.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Fall",
        "style": "Formal"
    },
    "12357.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Fall",
        "style": "Formal"
    },
    "12358.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Fall",
        "style": "Formal"
    },
    "12360.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "12361.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "12364.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "lightslategrey",
        "season": "Summer",
        "style": "Formal"
    },
    "12367.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "black",
        "season": "Fall",
        "style": "Casual"
    },
    "12368.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Fall",
        "style": "Formal"
    },
    "12369.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Fall",
        "style": "Formal"
    },
    "12371.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "burlywood",
        "season": "Summer",
        "style": "Casual"
    },
    "12372.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "silver",
        "season": "Fall",
        "style": "Formal"
    },
    "12374.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "12376.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "12378.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Fall",
        "style": "Casual"
    },
    "12380.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "darkgrey",
        "season": "Summer",
        "style": "Casual"
    },
    "12381.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "lavender",
        "season": "Summer",
        "style": "Formal"
    },
    "12383.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "13244.jpg": {
        "type": "Shorts",
        "gender": "Boys",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "13245.jpg": {
        "type": "Shorts",
        "gender": "Boys",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "13246.jpg": {
        "type": "Capris",
        "gender": "Girls",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "13247.jpg": {
        "type": "Leggings",
        "gender": "Women",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "13248.jpg": {
        "type": "Jeans",
        "gender": "Girls",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "13249.jpg": {
        "type": "Track Pants",
        "gender": "Women",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "13250.jpg": {
        "type": "Capris",
        "gender": "Women",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "13251.jpg": {
        "type": "Jeans",
        "gender": "Boys",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "13256.jpg": {
        "type": "Shirts",
        "gender": "Boys",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "13257.jpg": {
        "type": "Capris",
        "gender": "Girls",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "13259.jpg": {
        "type": "Jeans",
        "gender": "Women",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "13261.jpg": {
        "type": "Sweatshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "14774.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "darkgrey",
        "season": "Summer",
        "style": "Casual"
    },
    "14775.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "dimgray",
        "season": "Fall",
        "style": "Formal"
    },
    "14776.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "midnightblue",
        "season": "Fall",
        "style": "Formal"
    },
    "14777.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Fall",
        "style": "Formal"
    },
    "14778.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "lavender",
        "season": "Summer",
        "style": "Formal"
    },
    "14780.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "14781.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "14783.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "14784.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "rosybrown",
        "season": "Summer",
        "style": "Casual"
    },
    "14785.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "dimgray",
        "season": "Fall",
        "style": "Formal"
    },
    "14786.jpg": {
        "type": "Shirts",
        "gender": "Boys",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "15319.jpg": {
        "type": "Sweatshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Fall",
        "style": "Casual"
    },
    "15320.jpg": {
        "type": "Sweatshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Fall",
        "style": "Sports"
    },
    "15321.jpg": {
        "type": "Sweatshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Fall",
        "style": "Sports"
    },
    "15322.jpg": {
        "type": "Sweatshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Fall",
        "style": "Sports"
    },
    "15323.jpg": {
        "type": "Sweatshirts",
        "gender": "Men",
        "color": "dimgray",
        "season": "Fall",
        "style": "Casual"
    },
    "15324.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "15325.jpg": {
        "type": "Tshirts",
        "gender": "Boys",
        "color": "lightseagreen",
        "season": "Summer",
        "style": "Casual"
    },
    "15326.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "dimgray",
        "season": "Summer",
        "style": "Casual"
    },
    "15327.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "15329.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "15331.jpg": {
        "type": "Sports Shoes",
        "gender": "Women",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "15332.jpg": {
        "type": "Track Pants",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "15333.jpg": {
        "type": "Shorts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1543.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "1545.jpg": {
        "type": "Sports Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Sports"
    },
    "1634.jpg": {
        "type": "Sports Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1644.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "indianred",
        "season": "Summer",
        "style": "Sports"
    },
    "1645.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lightgray",
        "season": "Summer",
        "style": "Casual"
    },
    "1654.jpg": {
        "type": "Sports Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Sports"
    },
    "1844.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1845.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1852.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1853.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "khaki",
        "season": "Summer",
        "style": "Casual"
    },
    "1854.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "dimgray",
        "season": "Summer",
        "style": "Casual"
    },
    "1855.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "thistle",
        "season": "Summer",
        "style": "Casual"
    },
    "1857.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1859.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "indianred",
        "season": "Fall",
        "style": "Casual"
    },
    "1861.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "rosybrown",
        "season": "Summer",
        "style": "Casual"
    },
    "1862.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "gray",
        "season": "Summer",
        "style": "Casual"
    },
    "1865.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lavender",
        "season": "Summer",
        "style": "Casual"
    },
    "1867.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslateblue",
        "season": "Fall",
        "style": "Casual"
    },
    "1875.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lightseagreen",
        "season": "Fall",
        "style": "Casual"
    },
    "1880.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Fall",
        "style": "Casual"
    },
    "1881.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "silver",
        "season": "Fall",
        "style": "Casual"
    },
    "1884.jpg": {
        "type": "Shorts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1885.jpg": {
        "type": "Shorts",
        "gender": "Men",
        "color": "lightgray",
        "season": "Summer",
        "style": "Casual"
    },
    "1886.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "silver",
        "season": "Summer",
        "style": "Casual"
    },
    "1887.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "mediumseagreen",
        "season": "Summer",
        "style": "Casual"
    },
    "1888.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1889.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1890.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "tomato",
        "season": "Summer",
        "style": "Casual"
    },
    "1891.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "1892.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "royalblue",
        "season": "Summer",
        "style": "Casual"
    },
    "1895.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "1897.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "skyblue",
        "season": "Summer",
        "style": "Casual"
    },
    "1902.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "royalblue",
        "season": "Summer",
        "style": "Casual"
    },
    "2129.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2134.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Ethnic"
    },
    "2135.jpg": {
        "type": "Kurtas",
        "gender": "Women",
        "color": "saddlebrown",
        "season": "Summer",
        "style": "Ethnic"
    },
    "2138.jpg": {
        "type": "Kurtas",
        "gender": "Women",
        "color": "black",
        "season": "Summer",
        "style": "Ethnic"
    },
    "2266.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lightgreen",
        "season": "Summer",
        "style": "Casual"
    },
    "2268.jpg": {
        "type": "Tops",
        "gender": "Women",
        "color": "darkgrey",
        "season": "Summer",
        "style": "Casual"
    },
    "2269.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "tan",
        "season": "Summer",
        "style": "Casual"
    },
    "2270.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "hotpink",
        "season": "Summer",
        "style": "Casual"
    },
    "2272.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lightskyblue",
        "season": "Summer",
        "style": "Casual"
    },
    "2274.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2275.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "lavender",
        "season": "Summer",
        "style": "Casual"
    },
    "2276.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "slateblue",
        "season": "Summer",
        "style": "Casual"
    },
    "2278.jpg": {
        "type": "Tops",
        "gender": "Girls",
        "color": "lavender",
        "season": "Summer",
        "style": "Casual"
    },
    "2280.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "hotpink",
        "season": "Summer",
        "style": "Casual"
    },
    "2282.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2283.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Sports"
    },
    "2284.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "khaki",
        "season": "Summer",
        "style": "Sports"
    },
    "2285.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lightslategrey",
        "season": "Summer",
        "style": "Sports"
    },
    "2286.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2287.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lavender",
        "season": "Summer",
        "style": "Casual"
    },
    "2288.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2289.jpg": {
        "type": "Tshirts",
        "gender": "Girls",
        "color": "royalblue",
        "season": "Summer",
        "style": "Casual"
    },
    "2290.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "crimson",
        "season": "Summer",
        "style": "Casual"
    },
    "2291.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2292.jpg": {
        "type": "Tops",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2293.jpg": {
        "type": "Tshirts",
        "gender": "Women",
        "color": "hotpink",
        "season": "Summer",
        "style": "Casual"
    },
    "2294.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "salmon",
        "season": "Summer",
        "style": "Casual"
    },
    "2295.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "crimson",
        "season": "Summer",
        "style": "Casual"
    },
    "2296.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2297.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "mistyrose",
        "season": "Summer",
        "style": "Casual"
    },
    "2298.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "crimson",
        "season": "Summer",
        "style": "Sports"
    },
    "2299.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2300.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "mistyrose",
        "season": "Summer",
        "style": "Casual"
    },
    "2301.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "lavender",
        "season": "Summer",
        "style": "Casual"
    },
    "2302.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lavender",
        "season": "Summer",
        "style": "Casual"
    },
    "2303.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "mediumvioletred",
        "season": "Summer",
        "style": "Casual"
    },
    "2304.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "crimson",
        "season": "Summer",
        "style": "Sports"
    },
    "2305.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "mediumturquoise",
        "season": "Summer",
        "style": "Casual"
    },
    "2306.jpg": {
        "type": "Track Pants",
        "gender": "Women",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2307.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslateblue",
        "season": "Summer",
        "style": "Casual"
    },
    "2309.jpg": {
        "type": "Tops",
        "gender": "Girls",
        "color": "slateblue",
        "season": "Summer",
        "style": "Casual"
    },
    "2310.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "tomato",
        "season": "Summer",
        "style": "Sports"
    },
    "2311.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "deeppink",
        "season": "Summer",
        "style": "Sports"
    },
    "2312.jpg": {
        "type": "Shirts",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2313.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "mediumseagreen",
        "season": "Summer",
        "style": "Casual"
    },
    "2314.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2315.jpg": {
        "type": "Tshirts",
        "gender": "Boys",
        "color": "deeppink",
        "season": "Summer",
        "style": "Casual"
    },
    "2316.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "seagreen",
        "season": "Summer",
        "style": "Casual"
    },
    "2367.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2368.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2369.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2370.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2371.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2372.jpg": {
        "type": "Formal Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Formal"
    },
    "2373.jpg": {
        "type": "Formal Shoes",
        "gender": "Men",
        "color": "darkolivegreen",
        "season": "Summer",
        "style": "Formal"
    },
    "2374.jpg": {
        "type": "Formal Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2375.jpg": {
        "type": "Formal Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2376.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2377.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2378.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2379.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "black",
        "season": "Summer",
        "style": "Casual"
    },
    "2380.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2381.jpg": {
        "type": "Sports Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Sports"
    },
    "2382.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2387.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2389.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2397.jpg": {
        "type": "Sports Shoes",
        "gender": "Men",
        "color": "darkolivegreen",
        "season": "Summer",
        "style": "Sports"
    },
    "2398.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2399.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2727.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lightskyblue",
        "season": "Summer",
        "style": "Casual"
    },
    "2728.jpg": {
        "type": "Tops",
        "gender": "Boys",
        "color": "lightpink",
        "season": "Summer",
        "style": "Casual"
    },
    "2730.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "red",
        "season": "Summer",
        "style": "Casual"
    },
    "2732.jpg": {
        "type": "Tshirts",
        "gender": "Boys",
        "color": "gainsboro",
        "season": "Summer",
        "style": "Casual"
    },
    "2737.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "red",
        "season": "Summer",
        "style": "Casual"
    },
    "2801.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2820.jpg": {
        "type": "Casual Shoes",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "2821.jpg": {
        "type": "Sports Shoes",
        "gender": "Men",
        "color": "rosybrown",
        "season": "Summer",
        "style": "Sports"
    },
    "5450.jpg": {
        "type": "Shorts",
        "gender": "Girls",
        "color": "steelblue",
        "season": "Summer",
        "style": "Casual"
    },
    "5451.jpg": {
        "type": "Shorts",
        "gender": "Women",
        "color": "darkslateblue",
        "season": "Summer",
        "style": "Ethnic"
    },
    "5453.jpg": {
        "type": "Skirts",
        "gender": "Women",
        "color": "slategrey",
        "season": "Summer",
        "style": "Ethnic"
    },
    "5454.jpg": {
        "type": "Shorts",
        "gender": "Girls",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "5455.jpg": {
        "type": "Tshirts",
        "gender": "Boys",
        "color": "lightgray",
        "season": "Summer",
        "style": "Casual"
    },
    "5456.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "lightgray",
        "season": "Summer",
        "style": "Casual"
    },
    "8881.jpg": {
        "type": "Trousers",
        "gender": "Women",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "8883.jpg": {
        "type": "Jeans",
        "gender": "Women",
        "color": "gray",
        "season": "Summer",
        "style": "Ethnic"
    },
    "8885.jpg": {
        "type": "Trousers",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "9980.jpg": {
        "type": "Sweatshirts",
        "gender": "Men",
        "color": "black",
        "season": "Fall",
        "style": "Casual"
    },
    "9982.jpg": {
        "type": "Tops",
        "gender": "Men",
        "color": "midnightblue",
        "season": "Summer",
        "style": "Casual"
    },
    "9984.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "darkslategray",
        "season": "Summer",
        "style": "Casual"
    },
    "9985.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "midnightblue",
        "season": "Summer",
        "style": "Casual"
    },
    "9986.jpg": {
        "type": "Tshirts",
        "gender": "Men",
        "color": "midnightblue",
        "season": "Summer",
        "style": "Casual"
    }
}

# Recommendation criteria
criteria = {
    "season": "summer",
    "gender": "female",
    "color": "any",
    "style": "casual"
}

# Define the prompt
prompt = f"""
You are tasked with creating fashion style recommendations based on the user's wardrobe data and specific criteria. 

User wardrobe data:
{json.dumps(wardrobe_data, indent=2)}

Recommendation criteria:
{json.dumps(criteria, indent=2)}

Your goal is to generate complete style recommendations that meet the criteria provided. Each style should include a top, bottom, and shoes. Please ensure that the combinations are coherent and stylish. The output should be formatted as follows:

{{
    "style_1": {{
        "top": {{
            "image": "image_name.jpg",
            "type": "Top_Type",
            "gender": "Gender",
            "color": "Color",
            "season": "Season",
            "style": "Style"
        }},
        "bottom": {{
            "image": "image_name.jpg",
            "type": "Bottom_Type",
            "gender": "Gender",
            "color": "Color",
            "season": "Season",
            "style": "Style"
        }},
        "shoes": {{
            "image": "image_name.jpg",
            "type": "Shoes_Type",
            "gender": "Gender",
            "color": "Color",
            "season": "Season",
            "style": "Style"
        }}
    }},
    "style_2": {{
        // Another complete outfit recommendation
    }},
    "style_3": {{
        // Another complete outfit recommendation
    }}
}}

Please provide at least three style options that align with the given criteria.
"""


# Request completion from the model
completion = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=1500,
    top_p=1,
    stream=False,
    stop=None,
)


response_content = completion.choices[0].message['content'] if 'content' in completion.choices[0].message else completion.choices[0].message
print(response_content)

def extract_and_save_json(response_content, file_path):
    # Check if response_content is a ChatCompletionMessage object and extract content
    if hasattr(response_content, 'content'):
        response_content = response_content.content
    
    # Ensure response_content is now a string
    if isinstance(response_content, str):
        # Debugging: print the type and a snippet of the content
        print(f"response_content is of type {type(response_content)}")
        print(f"Snippet of response_content: {response_content[:200]}")
        
        # Use regex to extract the JSON content between ```json and ```
        match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        
        if match:
            json_content = match.group(1)
            
            # Convert the JSON content string to a dictionary
            json_data = json.loads(json_content)
            
            # Write the dictionary to a file as JSON
            with open(file_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            
            print(f"JSON content has been saved to {file_path}")
        else:
            print("No JSON content found in the response.")
    else:
        print(f"Expected a string, but got {type(response_content)}")

extract_and_save_json(response_content=response_content, file_path='D:/OSC/MirwearInterface/JSONstyles/style_recommendations.json')