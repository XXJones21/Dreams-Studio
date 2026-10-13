Decided instead of just live coding a basic web app, I'm providing two prompts that I would provide so that users can walk through building one.


## Natural Language Prompt

"Take a look at <link to repo> and let's build a complete web app around this Comfy Cloud workflow. A form exposes every creative input, the server submits one job, the page follows the job to the end, and the person can watch and download the film. Read through the `/workflows` and the `/docs` folder to get an understanding of how Comfy API is structured and what information would be nice to present to a user in a friendly user experience."

## Claude Specific prompts

These are pretty intense but aim to recreate what is already in the repo.

### Lightweight demo

```md
This repo has a ComfyUI workflow in workflows/dream_film.api.json, exported in API format. It turns a written dream into a short film on Comfy Cloud. I want to show that the API export alone is enough to build an app, so please only look at the workflows/ folder, not the rest of the repo.

Build the smallest Next.js app you can in examples/from-prompt-minimal/: a text box for the visual style, a "Make the film" button, and a video player that shows the film when it's done. Use @comfyorg/sdk version 0.4.0, and check its types in node_modules before you write calls against it.

The export already holds a full example dream, so you only need to set four inputs:
- the style text on node 2001,
- clip length "124" (a string) on node 2213, for the low-cost 5-second test,
- false on node 2201's switch, so it skips the image generator,
- workflows/default-keyframe.png as the image on node 8.

Pass the API key again when you submit, because the Partner Nodes inside the workflow need it. The film is the output from node 901.

Keep the key on the server in .env.local, and have the page poll the job every few seconds until it finishes. Please don't run a job yourself, since it spends credits. Just get it building and tell me how to start it.
```

### Full-size app

```md
This repo has a ComfyUI workflow in workflows/dream_film.api.json, exported in API format. It turns a written dream into a short first-person film on Comfy Cloud: a keyframe, three chained clips, and one stitched film. I want to show that the API export is enough to build a real app, so please only look at the workflows/ folder, not the rest of the repo.

Build a complete Next.js app in examples/from-prompt-studio/ using @comfyorg/sdk version 0.4.0. Check its types in node_modules before you write calls against it.

workflows/dream_film.inputs.json maps a name for each input and output to its node, so use those names instead of hard-coding node IDs. The form should cover all of them: style, keyframe scene, avoid, three clip actions, clip length, and a choice between generating the keyframe and uploading one. Fill the form with the example dream already in the export, so it works on first load.

A few things about this workflow you wouldn't guess:
- Clip length is sent as a string of frames, and only 124, 243 or 362 work (5, 10 or 15 seconds). Show seconds in the form.
- The Load Image node always needs a real file, even when the keyframe is generated, so fall back to workflows/default-keyframe.png.
- Randomize the four seeds on each run.
- Pass the API key again when you submit, because the Partner Nodes inside the workflow need it.
- Find outputs by node ID, not by their position in the list.

Keep the key on the server in .env.local, and check every request before it starts a paid job. Poll the job every few seconds, and remember the job ID in localStorage so a reload doesn't lose the film. Turn errors into a plain sentence (out of credits, bad key, and so on). When the film is done, show it with download buttons, and note that Comfy Cloud outputs expire.

Add a few tests that check the input map against the workflow without calling Comfy. Please don't run a job yourself, since it spends credits. Just get it building and tell me how to start it.
```