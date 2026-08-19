// This file sits at the project root, not beside its .resx in Resources/, and both facts matter.
//
// ResourceManagerStringLocalizerFactory builds the lookup name as
// RootNamespace + "." + ResourcesPath + "." + (type name minus root namespace), which for this
// type is Atelier.Web.Resources.SharedResource — matching the name MSBuild derives for a .resx
// from its folder. Put the class inside Resources/ instead and MSBuild pairs the two files and
// names the embedded resource after the *type* (Atelier.Web.SharedResource), so the two names no
// longer meet.
//
// The failure is silent, which is why it is written down: because the keys are the English
// strings, a missed lookup renders perfectly readable English. The only visible symptom was
// numbers formatted as "0,8°" — Spanish culture, English text — on a page that looked fine.
namespace Atelier.Web;

/// <summary>
/// Marker type for the shared string table. Nothing lives on it: it exists so that
/// <c>IStringLocalizer&lt;SharedResource&gt;</c> resolves to <c>Resources/SharedResource.*.resx</c>
/// from every component, instead of each component needing its own resource file.
///
/// Keys are the English strings themselves. A missing translation therefore falls back to
/// readable English rather than to a bare identifier — which is the failure mode that makes
/// half-localised apps look broken.
/// </summary>
public sealed class SharedResource
{
}
