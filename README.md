This repo is a simple python api endpoint that will generate bh configuration for the Diablo 2 Resurgence Mod.  Currently hosting via Google Cloud Run.

Will receive a set of post params then respond back with a complete bh.cfg file.

Navigate to repo root and build this, hit enter without changing the 1st option to use default service name (instructions I use, should be able to host it anywhere)
gcloud run deploy --source . --region us-west2
