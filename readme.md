# Readme

<img src="jil-sander-readme-photo-1.png" alt="Jil Sander S/S 2012" width="500">

## DISCLAIMER
This project is strictly for personal use and educational purposes. All content, including images and data, belongs to Vogue.

## What this repo can do as of right now

Sample is for Jil Sander Spring 2023 Ready to Wear.

It can get all the possible designers for season `spring-2012-ready-to-wear`, for example
```
https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear
```

It can get all the looks for combination of season `spring-2012-ready-to-wear` x designer `jil-sander`, for example
```
https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear/jil-sander/slideshow/collection#1
https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear/jil-sander/slideshow/collection#2
```

It can get all of the image urls for a combination of `spring-2012-ready-to-wear` x designer `jil-sander` x sub-section `collection#n`, for example

```
1,55c650ce08298d8be2167997,/fashion-shows/spring-2012-ready-to-wear/jil-sander/slideshow/collection#1,https://assets.vogue.com/photos/55c650ce08298d8be2167997/master/
175,55c650ce08298d8be2167ae4,/fashion-shows/spring-2012-ready-to-wear/jil-sander/slideshow/details#45,https://assets.vogue.com/photos/55c650ce08298d8be2167ae4/master/
```

It can save all the image urls to .jpg for a combination of `spring-2012-ready-to-wear` x designer `jil-sander` x sub-section `collection#n` (or `beauty#n` `front-row#n` `detail#n`), for example

<img src="jil-sander-readme-photo-2.png" alt="Jil Sander S/S 2012 Beauty" width="500">

## What this repo CANNOT do as of right now (AKA FUTURE WORK)

In descending importance.

It cannot do the following right now and **should** be improved to:

- Iteration & Caching: Iterate in a civilized manner across all seasons and across all designers. Iteration should be monitored and completed in a civilized manner without redoing a lot of work and raising flags to Vogue. Implement caching to avoid duplicating work.
- Retry logic: Implement retry mechanisms for failed requests or failed/incomplete processing. 
- Data retrieval and processing logging: Identify and log failures for future debugging.
- Tests/QA: 
    - Automated quality control checks to ensure we're not parsing nothing. 
    - Automated sample checks to ensure the right image is being attributed to the right designer, sub-section, et-cetera.
- User enhancements: 
    - Parse other information like Photographer, Model, general Vogue write-up of the whole collection.
    - Organize all data in a neat manner to easily search for something.
- Fun stuff:
    - Train diffusion model to make new images
    - Analysis: Trend analysis, trend forecasts, trend maps, trend timelines
    - Front end for display

## Rough outlook

a url is organized by fashion shows > season > designer > look

for example

https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear/

leads to 

https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear/jil-sander/

leads to 

https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear/jil-sander/slideshow/collection#21

leads to 2 images on this 21st look

https://assets.vogue.com/photos/55c650ce08298d8be21679ab/master/w_2240,c_limit/00210fullscreen.jpg

and

https://assets.vogue.com/photos/55c650ce08298d8be2167adb/master/w_2240,c_limit/00360fullscreen.jpg

seems that for each season x designer combination there is
text
collection (outfits with nested images)
details (with nested images)
beauty (with nested images)
front row (with nested images)

## Extracting image urls
It seems all of the necessary image urls are contained on a single page like
```
https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear/jil-sander/slideshow/collection#1
```
We parse every value after `"id":` for id, every value after `"url":` for url, every value after `"srcset":` for srcset.

Each id is associated with a unique image.

We can use it to build the image URL here.

```
https://assets.vogue.com/photos/{id}/master/
```

Each url is associated with the Collection Look, Detail Look, Beauty Look, or Front Row Look associated with the image url. For example, a single collection look (basically one outfit) can have a full body shot, a close up of the shoes or clothing items, basically multiple image urls can be associated with a url.

Should also decode unicode characters like \\u002F into readable format.

For example, from

```
\u002Ffashion-shows\u002Fspring-2012-ready-to-wear\u002Fjil-sander\u002Fslideshow\u002Fcollection#1
```

to

```
/fashion-shows/spring-2012-ready-to-wear/jil-sander/slideshow/collection#1
```
