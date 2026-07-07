Hi Duncan, 

it's been a while so I thought I'd check back if you found out anything about the cause of the [memory leak](http://stackoverflow.com/questions/23696391/memory-leak-when-using-package-xml-on-windows) when using `XML` on Windows.

I'm sure that you have got a thousand more interesting things to do, but I would just **so much** appreciate if you could fix this bug. It just keeps coming back at me and slows down all of my efforts WRT to Web Scraping. And given the fact that more and more cool packages emerge that depend on your package (e.g. [RSelenium](https://github.com/ropensci/RSelenium) or [rvest](https://github.com/hadley/rvest), this issue propagates to all of them as well.

Thank you so much,
Janko

---

Here is a slightly updated version of my investigations:
## Preliminaries

```
require("rvest")
require("XML")
```
## Functions

```
getTaskMemoryByPid <- function(
  pid = Sys.getpid()
) {
  cmd <- sprintf("tasklist /FI \"pid eq %s\" /FO csv", pid)
  mem <- read.csv(text=shell(cmd, intern = TRUE), stringsAsFactors=FALSE)[,5]
  mem <- as.numeric(gsub("\\.|\\s|K", "", mem))/1000
  mem
}  
getCurrentMemoryStatus <- function() {
  mem_os  <- getTaskMemoryByPid()
  mem_r   <- memory.size()
  prof_1  <- memory.profile()
  list(r = mem_r, os = mem_os, ratio = mem_os/mem_r)
}
memoryLeak <- function(
  x = system.file("exampleData", "mtcars.xml", package="XML"),
  n = 10000,
  use_text = FALSE,
  xpath = FALSE,
  free_doc = FALSE,
  clean_up = FALSE,
  detailed = FALSE,
  use_rvest = FALSE,
  user_agent = httr::user_agent("Mozilla/5.0")
) {
  if(use_text) {
    x <- readLines(x)
  }
  ## Before //
  prof_1  <- memory.profile()
  mem_before <- getCurrentMemoryStatus()

  ## Per run //
  mem_perrun <- lapply(1:n, function(ii) {
    doc <- if (!use_rvest) {
      xmlParse(x, asText = use_text)
    } else {
      if (file.exists(x)) {
      ## From disk //        
        rvest::html(x)  
      } else {
      ## From web //
        rvest::html_session(x, user_agent)  
      }
    }
    if (xpath) {
      res <- xpathApply(doc = doc, path = "/blah", fun = xmlValue)
      rm(res)
    }
    if (free_doc) {
      free(doc)
    }
    rm(doc)
    out <- NULL
    if (detailed) {
      out <- list(
        profile = memory.profile(),
        size = memory.size()
      )
    } 
    out
  })
  has_perrun <- any(sapply(mem_perrun, length) > 0)
  if (!has_perrun) {
    mem_perrun <- NULL
  } 

  ## Garbage collect //
  mem_gc <- NULL
  if(clean_up) {
    gc()
    tmp <- gc()
    mem_gc <- list(gc_mb = tmp["Ncells", "(Mb)"])
  }

  ## After //
  prof_2  <- memory.profile()
  mem_after <- getCurrentMemoryStatus()

  ## Return value //
  if (detailed) {
    list(
      before = mem_before, 
      perrun = mem_perrun, 
      gc = mem_gc, 
      after = mem_after, 
      comparison_r = data.frame(
        before = prof_1, 
        after = prof_2, 
        increase = round((prof_2/prof_1)-1, 4)
      ),
      increase_r = (mem_after$r/mem_before$r)-1,
      increase_os = (mem_after$os/mem_before$os)-1
    )
  } else {
    list(
      before_after = data.frame(
        r = c(mem_before$r, mem_after$r),
        os = c(mem_before$os, mem_after$os)
      ),
      increase_r = (mem_after$r/mem_before$r)-1,
      increase_os = (mem_after$os/mem_before$os)-1
    )
  }
}
```
## Memory status before anything has ever been requested

```
getCurrentMemoryStatus()
```
## Generate additional offline example content

```
s <- html_session("http://had.co.nz/")
tmp <- capture.output(httr::content(s$response))
write(tmp, file = "hadley.html")
# html("hadley.html")

s <- html_session(
  "http://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=ssd",
  httr::user_agent("Mozilla/5.0"))
tmp <- capture.output(httr::content(s$response))
write(tmp, file = "amazon.html")
# html("amazon.html")

getCurrentMemoryStatus()
```
## Profiling

```
################
## Mtcars.xml ##
################

res <- memoryLeak(n = 50000, detailed = FALSE)
fpath <- file.path(tempdir(), "memory-profile-1.1.rdata")
save(res, file = fpath)

res <- memoryLeak(n = 50000, clean_up = TRUE, detailed = FALSE)
fpath <- file.path(tempdir(), "memory-profile-1.2.rdata")
save(res, file = fpath)

res <- memoryLeak(n = 50000, clean_up = TRUE, free_doc = TRUE, detailed = FALSE)
fpath <- file.path(tempdir(), "memory-profile-1.3.rdata")
save(res, file = fpath)

###################
## www.had.co.nz ##
###################

## Offline //
res <- memoryLeak(x = "hadley.html", n = 50000, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-2.1.rdata")
save(res, file = fpath)

res <- memoryLeak(x = "hadley.html", n = 50000, clean_up = TRUE, 
  detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-2.2.rdata")
save(res, file = fpath)

res <- memoryLeak(x = "hadley.html", n = 50000, clean_up = TRUE, 
    free_doc = TRUE, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-2.3.rdata")
save(res, file = fpath)

## Online (PLEASE USE "POLITE" VALUE FOR `n`!!!) //
.url <- "http://had.co.nz/"
res <- memoryLeak(x = .url, n = 50, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-3.1.rdata")
save(res, file = fpath)

res <- memoryLeak(x = .url, n = 50, clean_up = TRUE, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-3.2.rdata")
save(res, file = fpath)

res <- memoryLeak(x = .url, n = 50, clean_up = TRUE, 
    free_doc = TRUE, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-3.3.rdata")
save(res, file = fpath)

####################
## www.amazon.com ##
####################

## Offline //
res <- memoryLeak(x = "amazon.html", n = 50000, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-4.1.rdata")
save(res, file = fpath)

res <- memoryLeak(x = "amazon.html", n = 50000, clean_up = TRUE, 
  detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-4.2.rdata")
save(res, file = fpath)

res <- memoryLeak(x = "amazon.html", n = 50000, clean_up = TRUE, 
    free_doc = TRUE, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-4.3.rdata")
save(res, file = fpath)

## Online (PLEASE USE "POLITE" VALUE FOR `n`!!!) //
.url <- "http://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=ssd"
res <- memoryLeak(x = .url, n = 50, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-4.1.rdata")
save(res, file = fpath)

res <- memoryLeak(x = .url, n = 50, clean_up = TRUE, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-4.2.rdata")
save(res, file = fpath)

res <- memoryLeak(x = .url, n = 50, clean_up = TRUE, 
    free_doc = TRUE, detailed = FALSE, use_rvest = TRUE)
fpath <- file.path(tempdir(), "memory-profile-4.3.rdata")
save(res, file = fpath)
```
