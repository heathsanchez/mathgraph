# Recon Report

## Verdict

`PROMOTE_LEAN_RECON`

## Decision

JSON:
{
  "verdict": "PROMOTE_LEAN_RECON",
  "issue": {
    "url": "https://github.com/omegahat/XML/issues/4",
    "title": "Still significant memory leak on Windows",
    "state": "OPEN",
    "labels": [],
    "comment_count": 3,
    "updatedAt": "2018-04-30T18:59:30Z"
  },
  "has_lean": true,
  "has_tests": true,
  "has_benchmark": true,
  "has_money": true,
  "has_surface": true,
  "risk": false
}

## Issue body excerpt

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


## Inventory excerpt

top files
.git/config
.git/description
.git/FETCH_HEAD
.git/HEAD
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/update.sample
.git/index
.git/info/exclude
.git/logs/HEAD
.git/ORIG_HEAD
.git/packed-refs
.Rbuildignore
addFinalizer
Aside.md
Bug.R
Bugs.html
Bugs/createXMLNode.R
Bugs/memory.R
Bugs/wormmart.R
Bugs/XMLStuff
ChangeLog
Check
checkLinks/big_checkLinks.R
checkLinks/checkLinks.R
checkLinks/other_checkLinks.R
cleanup
CodeDetails
configure
configure.ac
configure.win
Ctest/FOO
Ctest/GNUmakefile
Ctest/rogerK.c
Ctest/rogerK.R
Ctest/text.c
DESCRIPTION
DESCRIPTION.in
DiffWithCRAN
Docs/bibliog.bib
Docs/CreatingXML.xml
Docs/description.nw
Docs/description.xml
Docs/exercises.xml
Docs/GeneralHandlers.xml
Docs/GeneratingXML.nw
Docs/GNUmakefile
Docs/htmlTable.xml
Docs/InternalDOM.nw
Docs/job.xml
Docs/literate.nw
Docs/manual.nw
Docs/manual.xml
Docs/MathML.nw
Docs/MathML.xml
Docs/memory.tex
Docs/MemoryManagement.html
Docs/MemoryManagement.pdf
Docs/ModernDoc.html
Docs/ModernDoc.pdf
Docs/ModernDoc.Rdb
Docs/navigation.xml
Docs/OOP.nw
Docs/Outline.nw
Docs/Outline.xml
Docs/RS.xml
Docs/RSHelp.xml
Docs/RSXML.nw
Docs/RXML.xml
Docs/Schema.xml
Docs/shortIntro.xml
Docs/SSource.xml
Docs/Tour.nw
Docs/Tour.xml
Docs/WritingXML.html
dotCalls
expat/GNUmakefile
expat/GNUmakefile.lib
expat/xmlparse/GNUmakefile
expat/xmltok/GNUmakefile
FAQ.html
FIXME_NOW
getWinArchive.R
GNUmakefile
GNUmakefile.admin
index.html
index.html.in
inst/COPYRIGHTS
inst/exampleData/9003-en.html
inst/exampleData/9003.html
inst/exampleData/allNodeTypes.xml
inst/exampleData/author_invalid.xml
inst/exampleData/author.xml
inst/exampleData/author.xsd
inst/exampleData/author1.xml
inst/exampleData/author2.xml
inst/exampleData/author2.xsd
inst/exampleData/basic.xml
inst/exampleData/book.xml
inst/exampleData/boxplot.svg
inst/exampleData/branch.xml
inst/exampleData/catalog.xml
inst/exampleData/cdata.xml
inst/exampleData/charactersByEntity.xml
inst/exampleData/charts.svg
inst/exampleData/cleanNamespace.xml
inst/exampleData/content.html
inst/exampleData/dataframe.xml
inst/exampleData/dot.xml
inst/exampleData/dtd.zip
inst/exampleData/entity.xml
inst/exampleData/entity1.xml
inst/exampleData/entity2.xml
inst/exampleData/entity3.html
inst/exampleData/entity4.xml
inst/exampleData/entityValue
inst/exampleData/eurofxref-hist.xml.gz
inst/exampleData/event.xml
inst/exampleData/foo.dtd
inst/exampleData/functionTemplate.xml
inst/exampleData/generalInfo.xml
inst/exampleData/GNUmakefile
inst/exampleData/gnumeric.xml
inst/exampleData/graph.gxl
inst/exampleData/include.xml
inst/exampleData/iTunes.plist
inst/exampleData/job.xml
inst/exampleData/kiva_lender.xml
inst/exampleData/largeText.xml
inst/exampleData/lists.html
inst/exampleData/literate.dtd
inst/exampleData/literate.xml
inst/exampleData/literate.xsl
inst/exampleData/literateFunction.xml
inst/exampleData/longitudinalData.xml
inst/exampleData/malformed.xml
inst/exampleData/mathml.dtd
inst/exampleData/mathml.xml
inst/exampleData/mathmlFuncCall.xml
inst/exampleData/mathmlInt.xml
inst/exampleData/mathmlMatrix.xml
inst/exampleData/mathmlQuadratic.xml
inst/exampleData/mathmlRoot.xml
inst/exampleData/mathmlScript.xml
inst/exampleData/mathmlSet.xml
inst/exampleData/mathmlSimple.xml
inst/exampleData/mathmlSphere.xml
inst/exampleData/mathmlSums.xml
inst/exampleData/matrixMult.xml
inst/exampleData/mtcars.xml
inst/exampleData/namespaceHandlers.xml
inst/exampleData/namespaces.xml
inst/exampleData/namespaces1.xml
inst/exampleData/namespaces2.xml
inst/exampleData/nodes.xml
inst/exampleData/nodes1.xml
inst/exampleData/nodes2.xml
inst/exampleData/nodes3.xml
inst/exampleData/nsAttrs.xml
inst/exampleData/plist.xml
inst/exampleData/raw.xml
inst/exampleData/README
inst/exampleData/redundantNS.xml
inst/exampleData/reparent.xml
inst/exampleData/rhelp.xsl
inst/exampleData/Rref.xml
inst/exampleData/Rsource.xml
inst/exampleData/rxinclude.xml
inst/exampleData/same.xml
inst/exampleData/setInterval.xml
inst/exampleData/simple.plist
inst/exampleData/simple.xml
inst/exampleData/size.xml
inst/exampleData/size1.xml
inst/exampleData/size2.xml
inst/exampleData/size3.xml
inst/exampleData/SOAPNamespaces.xml
inst/exampleData/solr.xml
inst/exampleData/something.xml
inst/exampleData/StatModel.dtd
inst/exampleData/svg.xml
inst/exampleData/symslines.svg
inst/exampleData/tagnames.xml
inst/exampleData/test.xml
inst/exampleData/test1.xml
inst/exampleData/TestInvalid.xml
inst/exampleData/tides.xml
inst/exampleData/utf.xml
inst/exampleData/vars.xml
inst/exampleData/writeRS.S
inst/exampleData/writeRS.xml
inst/exampleData/xpathTest.xml
inst/exampleData/xysize.svg
inst/exampleData/xyz.svg.gz
inst/examples/A.xml
inst/examples/author.R
inst/examples/B.xml
inst/examples/bondsTables.R
inst/examples/bondYields.R
inst/examples/C.xml
inst/examples/catalog.R
inst/examples/CIS.R
inst/examples/connections.R
inst/examples/connections1.R
inst/examples/createTree.R
inst/examples/createTree1.R
inst/examples/dataFrameEvent.R
inst/examples/DatasetByRecord.dtd
inst/examples/DiGIR.R
inst/examples/docbook.R
inst/examples/ecb.R
inst/examples/enhancedDataFrame.R
inst/examples/event.R
inst/examples/event.S
inst/examples/eventHandlers.R
inst/examples/faq.R
inst/examples/filterDataFrameEvent.R
inst/examples/foo.html
inst/examples/formals.xsl
inst/examples/functionIndex.Sxml
inst/examples/generic_file.xml
inst/examples/genericHandlers.R
inst/examples/getElements.S
inst/examples/gettingStarted.html
inst/examples/gettingStarted.xml
inst/examples/GNUmakefile
inst/examples/gnumericHandler.R
inst/examples/hashTree.R
inst/examples/HTMLText.R
inst/examples/index.html
inst/examples/internalNodes.S
inst/examples/internalXInclude.xml
inst/examples/iTunes.plist
inst/examples/itunes.R
inst/examples/itunes.xml
inst/examples/itunes.xsl
inst/examples/itunesSax.R
inst/examples/itunesSax1.R
inst/examples/itunesSax2.R
inst/examples/mathml.R
inst/examples/mathmlPlot.R
inst/examples/metlin.R
inst/examples/mexico.R
inst/examples/mexico.xml
inst/examples/mi1.R
inst/examples/modified_itunes_sax.R
inst/examples/multi.md
inst/examples/multi.xml
inst/examples/namespaces.S
inst/examples/namespaces1.S
inst/examples/newNodes.R
inst/examples/oop.S
inst/examples/other.xml
inst/examples/pi.xml
inst/examples/pmml.R
inst/examples/prompt.xml
inst/examples/promptXML.R
inst/examples/promptXML.Sxml
inst/examples/rcode.xml
inst/examples/rcode.xsl
inst/examples/README
inst/examples/redirection.R
inst/examples/reorder.xml
inst/examples/Rhelp.xml
inst/examples/RhelpArchive.xml
inst/examples/RhelpInfo.xml
inst/examples/SAXEntity.R
inst/examples/sbml.xml
inst/examples/sbmlSAX.S
inst/examples/schema.xsd
inst/examples/schemaEg.xml
inst/examples/schemas.xml
inst/examples/SSource.dtd
inst/examples/svg.R
inst/examples/tags.Sxml
inst/examples/trademe_cars.R
inst/examples/valueFilterDataFrameEvent.R
inst/examples/wordML.R
inst/examples/writeExamples.S
inst/examples/X.xml
inst/examples/xml2tex.Sxml
inst/examples/xmlSource.R
inst/examples/xmlTags.xml
inst/examples/xmlTree.R
inst/examples/xpath.R
inst/examples/xpath.xml
inst/examples/Y.xml
inst/examples/yeast_small-01.xml
inst/scripts/RSXML.bsh.in
inst/scripts/RSXML.csh.in
INSTALL_R
INSTALL_S
Install/configure
Install/configureInstall
Install/configureInstall.in
Install/GNUmakefile.admin
Install/GNUmakefile.Splus.in
Install/INSTALL
Install/INSTALL.in
Install/Web/configure
Install/Web/configure.in
Install/Web/GNUmakefile
Install/Web/index.html
Install/Web/index.html.in
Install/Web/README
Install/Web/Requirements.html
libxml/GNUmakefile
libxml/PATCH.attribute
LICENSE
man/addChildren.Rd
man/addNode.Rd
man/addSibling.Rd
man/append.XMLNode.Rd
man/AssignXMLNode.Rd
man/asXMLNode.Rd
man/asXMLTreeNode.Rd
man/catalogResolve.Rd
man/catalogs.Rd
man/coerce.Rd
man/compareXMLDocs.Rd
man/docName.Rd
man/Doctype-class.Rd
man/Doctype.Rd
man/dtdElement.Rd
man/dtdElementValidEntry.Rd
man/dtdIsAttribute.Rd
man/dtdValidElement.Rd
man/ensureNamespace.Rd
man/findXInclude.Rd
man/fixDocXIncludes.Rd
man/free.Rd
man/genericSAXHandlers.Rd
man/getChildrenStrings.Rd
man/getEncoding.Rd
man/getHTMLLinks.Rd
man/getLineNumber.Rd
man/getNodeSet.Rd
man/getRelativeURL.Rd
man/getXIncludes.Rd
man/getXMLErrors.Rd
man/isXMLString.Rd
man/length.XMLNode.Rd
man/libxmlVersion.Rd
man/makeClassTemplate.Rd
man/names.XMLNode.Rd
man/newXMLDoc.Rd
man/newXMLNamespace.Rd
man/parseDTD.Rd
man/parseURI.Rd
man/parseXMLAndAdd.Rd
man/print.Rd
man/processXInclude.Rd
man/readHTMLList.Rd
man/readHTMLTable.Rd
man/readKeyValueDB.Rd
man/readSolrDoc.Rd
man/removeXMLNamespaces.Rd
man/replaceNodeWithChildren.Rd
man/saveXML.Rd
man/SAXMethods.Rd
man/SAXState-class.Rd
man/schema-class.Rd
man/setXMLNamespace.Rd
man/supportsExpat.Rd
man/toHTML.Rd
man/xmlApply.Rd
ma

## Grep excerpt

===== judge hits =====
./man/XMLInternalDocument.Rd:25:  find nodes within a document that satisfy some criterion.
./man/getNodeSet.Rd:9:  criterion. It uses the XPath syntax and allows very powerful
./index.html:115:This XML-approach is in contrast to a simple ASCII or native object dump which relies
./index.html:117:(Communicating via the S4 object ASCII dump format was used
./configure:2196:char const utf8_literal[] = u8"happens to be ASCII" "another string";
./FIXME_NOW:17:[done] getNodeSet now failing if it returns nothing.
./Todo.xml:216:replaceNodes seems to be failing here.
./Problems/test.mzXML:32:    pairOrder="m/z-int" >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

