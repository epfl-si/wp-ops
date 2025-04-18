<?php

// Template for the 500 error page.

?>
<!doctype html>
<html lang="en">

<head>
  <title>Internal server error - EPFL</title>
  <meta charset="utf-8" />
  <meta name="description" content="Internal server error - EPFL" />

  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#ff0000">

  <link rel="shortcut icon" type="image/x-icon" href="//web2018.epfl.ch/5.1.1/icons/favicon.ico">
  <link rel="icon" type="image/png" sizes="16x16" href="//web2018.epfl.ch/5.1.1/icons/favicon-16.png">
  <link rel="icon" type="image/png" sizes="32x32" href="//web2018.epfl.ch/5.1.1/icons/favicon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="//web2018.epfl.ch/5.1.1/icons/apple-touch-icon.png">

  <link rel="stylesheet" href="//web2018.epfl.ch/5.1.1/css/elements.min.css">

  <script async src="https://www.googletagmanager.com/gtag/js?id=UA-4833294-1"></script>
  <script>
    window.dataLayer = window.dataLayer || [];

    function gtag() {
      dataLayer.push(arguments);
    }
    gtag('js', new Date());
    gtag('config', 'UA-4833294-1', {
      'anonymize_ip': true
    });
  </script>

</head>

<body>
  <div class="site d-flex flex-column min-vh-100">

    <nav class="access-nav" aria-label="Navigation shortcuts">
      <ul>
        <li>
          <a class="btn btn-primary" href="/" title="[ALT + 1]" accesskey="1">Homepage of the site</a>
        </li>
        <li>
          <a class="btn btn-primary" href="#main" title="[ALT + 2]" accesskey="2">Skip to content</a>
        </li>
        <li>
          <a class="btn btn-primary" href="#main-navigation" title="[ALT + 3]" accesskey="3">Skip to main navigation</a>
        </li>
        <li>
          <a class="btn btn-primary" href="#nav-aside" title="[ALT + 4]" accesskey="4">Skip to side navigation</a>
        </li>
        <li>
          <a class="btn btn-primary" href="#q" title="[ALT + 5]" accesskey="5">Skip to search</a>
        </li>
        <li>
          <a class="btn btn-primary" href="mailto:1234@epfl.ch" title="[ALT + 6]" accesskey="6">Contact us</a>
        </li>
      </ul>
    </nav>

    <header class="header">
      <a class="logo" href="/">
        <img src="//web2018.epfl.ch/5.1.1/icons/epfl-logo.svg" alt="Logo EPFL, Ecole polytechnique fédérale de Lausanne" class="img-fluid">
      </a>
    </header>

    <div class="breadcrumb-container">
      <nav aria-label="breadcrumb" class="breadcrumb-wrapper" id="breadcrumb-wrapper">
        <ol class="breadcrumb">
          <li class="breadcrumb-item">
            <a href="//www.epfl.ch" title="Home" aria-label="Home">
              <svg class="icon" aria-hidden="true">
                <use xlink:href="#icon-home"></use>
              </svg>
            </a>
          </li>
          <li class="breadcrumb-item active" aria-current="page"><?php echo $statuses[$st]; ?></li>
        </ol>
      </nav>
    </div>

    <div class="main-container">
      <p class="w-100 pb-5">
      <main id="main" class="content container">
        <h1 class="mb-5"><?php echo $statuses[$st]; ?></h1>
        <p>
          The server encountered an unexpected error and was unable to respond to your request. Please try again later.
        </p>
        <?php include("debug.php") ?>

      </main>
    </div>
    <div class="bg-gray-100 pt-5 mt-auto">
      <div class="container">
        <footer class="footer-light">
          <div class="row">
            <div class="col-6 mx-auto mx-md-0 mb-4 col-md-3 col-lg-2">
              <a href="//www.epfl.ch">
                <img src="//web2018.epfl.ch/5.1.1/icons/epfl-logo.svg" alt="Logo EPFL, Ecole polytechnique fédérale de Lausanne" class="img-fluid">
              </a>
            </div>
            <div class="col-md-9 col-lg-10 mb-4">
              <div class="ml-md-2 ml-lg-5">
                <ul class="list-inline list-unstyled">
                  <li class="list-inline-item">Contact</li>
                  <li class="list-inline-item text-muted pl-3"><small>EPFL CH-1015 Lausanne</small></li>
                  <li class="list-inline-item text-muted pl-3"><small>+41 21 693 11 11</small></li>
                </ul>
                <p class="footer-light-socials">
                  <small>Follow the pulses of EPFL on social networks</small>
                  <span>
                    <a href="https://www.facebook.com/epflcampus" class="social-icon social-icon-facebook social-icon-negative" rel="noopener" target="_blank">
                      <svg class="icon" aria-hidden="true">
                        <use xlink:href="#icon-facebook"></use>
                      </svg>
                      <span class="sr-only">Follow us on Facebook.</span>
                    </a>
                    <a href="https://twitter.com/epfl_en" class="social-icon social-icon-twitter social-icon-negative" rel="noopener" target="_blank">
                      <svg class="icon" aria-hidden="true">
                        <use xlink:href="#icon-twitter"></use>
                      </svg>
                      <span class="sr-only">Follow us on Twitter.</span>
                    </a>
                    <a href="https://instagram.com/epflcampus" class="social-icon social-icon-instagram social-icon-negative" rel="noopener" target="_blank">
                      <svg class="icon" aria-hidden="true">
                        <use xlink:href="#icon-instagram"></use>
                      </svg>
                      <span class="sr-only">Follow us on Instagram.</span>
                    </a>
                    <a href="https://www.youtube.com/user/epflnews" class="social-icon social-icon-youtube social-icon-negative" rel="noopener" target="_blank">
                      <svg class="icon" aria-hidden="true">
                        <use xlink:href="#icon-youtube"></use>
                      </svg>
                      <span class="sr-only">Follow us on Youtube.</span>
                    </a>
                    <a href="https://www.linkedin.com/school/epfl/" class="social-icon social-icon-linkedin social-icon-negative" rel="noopener" target="_blank">
                      <svg class="icon" aria-hidden="true">
                        <use xlink:href="#icon-linkedin"></use>
                      </svg>
                      <span class="sr-only">Follow us on LinkedIn.</span>
                    </a>
                  </span>
                </p>
                <div class="footer-legal">
                  <div class="footer-legal-links">
                    <a href="//www.epfl.ch/accessibility.en.shtml">Accessibility</a>
                    <a href="//www.epfl.ch/about/overview/overview/regulations-and-guidelines/">Legal notice</a>
                    <a href="//go.epfl.ch/privacy-policy/">Privacy Policy</a>
                  </div>
                  <div>
                    <p>&copy; 2025 EPFL, all rights reserved</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </footer>

        <button id="back-to-top" class="btn btn-primary btn-back-to-top">
          <span class="sr-only">Back to top</span>
          <svg class="icon" aria-hidden="true">
            <use xlink:href="#icon-chevron-top"></use>
          </svg>
        </button>
      </div>
    </div>
  </div>
  </div>

  <script>
    svgPath = 'https://web2018.epfl.ch/5.1.1/icons/icons.svg';
    featherSvgPath = 'https://web2018.epfl.ch/5.1.1/icons/feather-sprite.svg';
  </script>

  <script src="//web2018.epfl.ch/5.1.1/js/elements.min.js"></script>
</body>

</html>
