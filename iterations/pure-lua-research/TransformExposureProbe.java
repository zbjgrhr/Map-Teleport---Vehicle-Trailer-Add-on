import java.util.Arrays;
import org.joml.Vector3f;
import zombie.core.physics.Transform;
import zombie.Lua.LuaManager;
import se.krka.kahlua.converter.KahluaConverterManager;
import se.krka.kahlua.j2se.J2SEPlatform;
import se.krka.kahlua.vm.*;
import se.krka.kahlua.luaj.compiler.LuaCompiler;
public class TransformExposureProbe {
 public static void main(String[] args) throws Exception {
  var platform=J2SEPlatform.getInstance();
  var env=platform.newEnvironment();
  var exposer=new LuaManager.Exposer(new KahluaConverterManager(),platform,env);
  exposer.setExposed(Transform.class);exposer.setExposed(Vector3f.class);
  exposer.exposeLikeJavaRecursively(Transform.class,env);
  exposer.exposeLikeJavaRecursively(Vector3f.class,env);
  var code=LuaCompiler.loadstring("local t=Transform.new(); local v=t:getOrigin(); v:set(10,20,30); return v:x(),v:y(),v:z(),type(t.set),type(t.setIdentity)","probe",env);
  var thread=new KahluaThread(platform,env); thread.debugOwnerThread=Thread.currentThread(); var result=thread.pcall(code,new Object[0]);
  System.out.println(Arrays.toString(result));
  if (!Boolean.TRUE.equals(result[0])) throw new AssertionError("Native Lua exposure failed");
 }
}
