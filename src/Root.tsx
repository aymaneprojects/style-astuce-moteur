import {Composition} from 'remotion';
import {Episode} from './Episode';
// Les données viennent de --props=out/<episode>/props.json (construit par « python3 cli/sa.py timeline »).
export const RemotionRoot = () => (
  <Composition id="Episode" component={Episode as any} fps={30} width={1080} height={1920} durationInFrames={300}
    defaultProps={{data: null}}
    calculateMetadata={({props}: any) => ({durationInFrames: props.data.total, props})} />
);
